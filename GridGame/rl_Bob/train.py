import torch
import torch.optim as optim
import torch.nn.functional as F
from torch_geometric.data import Data, Batch
import argparse
import os
import random
from collections import Counter, deque
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from model import GraphColoringDQN
from ColoringEnv import ColoringEnv

def save_checkpoint(path, model, optimizer, episode_idx, config):
    # Ensure directory exists before saving
    checkpoint_dir = os.path.dirname(path)
    if checkpoint_dir:
        os.makedirs(checkpoint_dir, exist_ok=True)
    checkpoint = {
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "episode": episode_idx,
        "config": config,
    }
    torch.save(checkpoint, path)

def load_checkpoint(path, model, optimizer=None, device="cpu"):
    # Load model and optimizer states
    checkpoint = torch.load(path, map_location=device)
    model.load_state_dict(checkpoint["model_state_dict"])
    if optimizer is not None and "optimizer_state_dict" in checkpoint:
        optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
    return checkpoint

def log_metrics_to_file(log_path, episode_idx, num_episodes, win_rate, min_episode_return, 
                         avg_episode_return, max_episode_return, avg_episode_length,
                         dqn_loss, HEIGHT, WIDTH, COLORS):
    # Write metrics to log
    log_dir = os.path.dirname(log_path)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    
    file_exists = os.path.exists(log_path)
    with open(log_path, 'a') as f:
        if not file_exists or episode_idx <= num_episodes:
            f.write(f"Bob Training On size: w={WIDTH}, h={HEIGHT}, c={COLORS}\n")
            f.write("episode,num_episodes,win_rate,min_score,avg_score,max_score,avg_length,dqn_loss\n")
        if num_episodes > 0:
            f.write(f"{episode_idx},{num_episodes},{win_rate:.4f},{min_episode_return:.4f},{avg_episode_return:.4f},"
                f"{max_episode_return:.4f},{avg_episode_length:.4f},{dqn_loss:.6f}\n")

def get_action(state, policy_net, epsilon):
    # Epsilon-greedy selection
    mask = state["mask"]
    valid_actions = torch.where(mask)[0]
    
    if len(valid_actions) == 0:
        return None 
        
    if random.random() < epsilon:
        action = random.choice(valid_actions.tolist())
    else:
        with torch.no_grad():
            q_values = policy_net(state["x"], state["edge_index"], batch_size=1)
            masked_q_values = q_values[0].masked_fill(~mask, float('-inf'))
            action = masked_q_values.argmax().item()
            
    return action

def main():
    # Setup configuration
    script_dir = Path(__file__).parent.parent 
    default_checkpoint = str(script_dir / "checkpoints" / "Bob" / "latest.pt")
    default_log_file = str(script_dir / "checkpoints" / "Bob" / "training_metrics.csv")
    
    parser = argparse.ArgumentParser(description="Train GNN-DQN graph coloring agent.")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint.")
    parser.add_argument("--checkpoint-path", type=str, default=default_checkpoint, help="Path to checkpoint file.")
    parser.add_argument("--log-path", type=str, default=default_log_file, help="Path to metrics log file.")
    parser.add_argument("--save-every", type=int, default=500, help="Save checkpoint every N episodes.")
    args = parser.parse_args()

    WIDTH, HEIGHT, COLORS = 5, 5, 4
    LEARNING_RATE = 1e-3
    GAMMA = 0.95
    EPSILON_START = 1.0
    EPSILON_END = 0.05
    EPSILON_DECAY = 0.995
    BATCH_SIZE = 64
    MEMORY_SIZE = 50000
    TOTAL_EPISODES = 10_000
    TARGET_UPDATE = 50
    LOG_INTERVAL = 100
    
    env = ColoringEnv(width=WIDTH, height=HEIGHT, num_colors=COLORS)
    
    # Feature size updated to match coordinates addition (Classes + X + Y)
    num_node_features = (COLORS + 1) + 2
    policy_net = GraphColoringDQN(num_node_features, hidden_size=64, num_colors=COLORS)
    target_net = GraphColoringDQN(num_node_features, hidden_size=64, num_colors=COLORS)
    target_net.load_state_dict(policy_net.state_dict())
    target_net.eval()

    optimizer = optim.Adam(policy_net.parameters(), lr=LEARNING_RATE)
    memory = deque(maxlen=MEMORY_SIZE)
    epsilon = EPSILON_START

    config = {
        "width": WIDTH,
        "height": HEIGHT,
        "colors": COLORS,
        "learning_rate": LEARNING_RATE,
        "batch_size": BATCH_SIZE,
        "gamma": GAMMA,
    }

    start_episode = 1
    if args.resume and os.path.exists(args.checkpoint_path):
        checkpoint = load_checkpoint(args.checkpoint_path, policy_net, optimizer)
        start_episode = int(checkpoint.get("episode", 0)) + 1

    completed_episodes_data = []
    recent_losses = []

    for episode in range(start_episode, TOTAL_EPISODES + 1):
        state = env.reset()
        total_reward = 0
        steps = 0
        done = False
        episode_loss = 0
        
        while not done:
            action = get_action(state, policy_net, epsilon)
            if action is None:
                done = True
                reason = "no_valid_moves"
                break
                
            next_state, reward, done = env.step(action)
            total_reward += reward
            steps += 1
            
            memory.append((state, action, reward, next_state, done))
            state = next_state
            
            # Vectorized optimization step using PyG Batch
            if len(memory) >= BATCH_SIZE:
                batch_data = random.sample(memory, BATCH_SIZE)
                
                # Prepare graph structures
                states_list = [Data(x=b[0]["x"], edge_index=b[0]["edge_index"]) for b in batch_data]
                next_states_list = [Data(x=b[3]["x"], edge_index=b[3]["edge_index"]) for b in batch_data]
                
                batched_states = Batch.from_data_list(states_list)
                batched_next_states = Batch.from_data_list(next_states_list)
                
                # Prepare tensors
                actions = torch.tensor([b[1] for b in batch_data], dtype=torch.long)
                rewards = torch.tensor([b[2] for b in batch_data], dtype=torch.float32)
                dones = torch.tensor([b[4] for b in batch_data], dtype=torch.bool)
                
                next_masks = torch.stack([b[3]["mask"] for b in batch_data])

                # Get current Q values
                all_q_values = policy_net(batched_states.x, batched_states.edge_index, batch_size=BATCH_SIZE)
                q_values = all_q_values.gather(1, actions.unsqueeze(1)).squeeze(1)
                
                # Get target Q values
                with torch.no_grad():
                    next_all_q_values = target_net(batched_next_states.x, batched_next_states.edge_index, batch_size=BATCH_SIZE)
                    next_masked_q = next_all_q_values.masked_fill(~next_masks, float('-inf'))
                    
                    max_next_q = next_masked_q.max(dim=1)[0]
                    max_next_q = torch.where(torch.isinf(max_next_q), torch.zeros_like(max_next_q), max_next_q)
                    
                    targets = rewards + GAMMA * max_next_q * (~dones).float()
                
                # Compute loss and step
                loss = F.smooth_l1_loss(q_values, targets)
                
                optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(policy_net.parameters(), max_norm=0.5)
                optimizer.step()
                
                episode_loss += loss.item()
                
        if reward >= 10.0: reason = "bob_wins"
        elif reward <= -10.0: reason = "bob_loses"
        else: reason = "timeout"

        completed_episodes_data.append({"return": total_reward, "length": steps, "reason": reason})
        if steps > 0: recent_losses.append(episode_loss / steps)
            
        epsilon = max(EPSILON_END, epsilon * EPSILON_DECAY)
        
        if episode % TARGET_UPDATE == 0:
            target_net.load_state_dict(policy_net.state_dict())
            
        if episode % LOG_INTERVAL == 0:
            num_episodes_log = len(completed_episodes_data)
            returns = [ep["return"] for ep in completed_episodes_data]
            reasons = Counter(ep["reason"] for ep in completed_episodes_data)
            
            avg_loss = sum(recent_losses) / len(recent_losses) if recent_losses else 0
            print(f"Episode {episode:5d} | DQN Loss: {avg_loss: 8.3f}")
            
            completed_episodes_data.clear()
            recent_losses.clear()
            
            if args.save_every > 0 and episode % args.save_every == 0:
                save_checkpoint(args.checkpoint_path, policy_net, optimizer, episode, config)

    save_checkpoint(args.checkpoint_path, policy_net, optimizer, episode, config)

if __name__ == "__main__":
    main()