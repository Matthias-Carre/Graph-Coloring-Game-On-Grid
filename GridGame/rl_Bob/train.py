import torch
import torch.optim as optim
import torch.nn.functional as F
import argparse
import os
import random
from collections import Counter, deque
import sys
from pathlib import Path

# Add parent directory to path to access game modules
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
    # Load model and optimizer states from a file
    checkpoint = torch.load(path, map_location=device)
    model.load_state_dict(checkpoint["model_state_dict"])
    if optimizer is not None and "optimizer_state_dict" in checkpoint:
        optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
    return checkpoint

def log_metrics_to_file(log_path, episode_idx, num_episodes, win_rate, min_episode_return, 
                         avg_episode_return, max_episode_return, avg_episode_length,
                         dqn_loss, HEIGHT, WIDTH, COLORS):
    # Logs training metrics to a CSV file for later analysis
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

def run_evaluation_episode(policy_net, env):
    # Runs one evaluation episode to print the final grid state
    print("\n" + "="*30)
    print("EVALUATION: FINAL GRID")
    print("="*30)
    
    state = env.reset()
    done = False
    total_reward = 0.0
    reason = "Unknown"
    
    while not done:
        # Query policy for the best action (exploit only, epsilon=0)
        action = get_action(state, policy_net, epsilon=0.0)
        if action is None:
            reason = "No valid moves"
            break
            
        state, reward, done = env.step(action)
        total_reward += reward
        
        if done:
            if reward >= 10.0:
                reason = "bob_wins"
            else:
                reason = "alice_wins / grid_full"
        
    # Print the raw grid array to visualize the final state
    print(f"Final Grid Array: {env.grid}")
    print(f"End Reason: {reason} | Final Reward: {total_reward:.2f}")
    print("="*30 + "\n")

def get_action(state, policy_net, epsilon):
    # Epsilon-greedy logic with action masking
    mask = state["mask"]
    valid_actions = torch.where(mask)[0]
    
    if len(valid_actions) == 0:
        return None 
        
    if random.random() < epsilon:
        action = random.choice(valid_actions.tolist())
    else:
        with torch.no_grad():
            q_values = policy_net(state["x"], state["edge_index"])
            masked_q_values = q_values.masked_fill(~mask, float('-inf'))
            action = masked_q_values.argmax().item()
            
    return action

def main():
    # Setup paths and arguments
    script_dir = Path(__file__).parent.parent 
    default_checkpoint = str(script_dir / "checkpoints" / "Bob" / "latest.pt")
    default_log_file = str(script_dir / "checkpoints" / "Bob" / "training_metrics.csv")
    
    parser = argparse.ArgumentParser(description="Train GNN-DQN graph coloring agent.")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint.")
    parser.add_argument("--checkpoint-path", type=str, default=default_checkpoint, help="Path to checkpoint file.")
    parser.add_argument("--log-path", type=str, default=default_log_file, help="Path to metrics log file.")
    parser.add_argument("--save-every", type=int, default=500, help="Save checkpoint every N episodes.")
    args = parser.parse_args()

    # Hyperparameters
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
    
    print("Initializing environment...")
    env = ColoringEnv(width=WIDTH, height=HEIGHT, num_colors=COLORS)
    eval_env = ColoringEnv(width=WIDTH, height=HEIGHT, num_colors=COLORS)

    print("Creating GNN-DQN network...")
    num_node_features = COLORS + 1
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
    if args.resume:
        if os.path.exists(args.checkpoint_path):
            checkpoint = load_checkpoint(args.checkpoint_path, policy_net, optimizer, device="cpu")
            start_episode = int(checkpoint.get("episode", 0)) + 1
            print(f"Resumed from {args.checkpoint_path} at episode {start_episode}")
        else:
            print(f"Checkpoint not found at {args.checkpoint_path}. Starting fresh.")

    print("Starting training loop...\n")
    
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
            
            # Optimization step
            if len(memory) >= BATCH_SIZE:
                batch = random.sample(memory, BATCH_SIZE)
                loss = 0
                for b_state, b_action, b_reward, b_next_state, b_done in batch:
                    q_values = policy_net(b_state["x"], b_state["edge_index"])
                    q_value = q_values[b_action]
                    
                    if b_done:
                        target = torch.tensor(b_reward, dtype=torch.float32)
                    else:
                        with torch.no_grad():
                            next_q_values = target_net(b_next_state["x"], b_next_state["edge_index"])
                            next_masked_q = next_q_values.masked_fill(~b_next_state["mask"], float('-inf'))
                            if torch.isinf(next_masked_q).all():
                                target = torch.tensor(b_reward, dtype=torch.float32)
                            else:
                                target = b_reward + GAMMA * next_masked_q.max()
                                
                    loss += F.smooth_l1_loss(q_value, target)
                
                loss = loss / BATCH_SIZE
                optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(policy_net.parameters(), max_norm=0.5)
                optimizer.step()
                
                episode_loss += loss.item()
                
        # Deduce end reason
        if reward >= 10.0:
            reason = "bob_wins"
        elif reward <= -10.0:
            reason = "bob_loses"
        else:
            reason = "timeout"

        # Record episode data
        completed_episodes_data.append({
            "return": total_reward,
            "length": steps,
            "reason": reason
        })
        if steps > 0:
            recent_losses.append(episode_loss / steps)
            
        epsilon = max(EPSILON_END, epsilon * EPSILON_DECAY)
        
        if episode % TARGET_UPDATE == 0:
            target_net.load_state_dict(policy_net.state_dict())
            
        # Logging metrics and evaluation
        if episode % LOG_INTERVAL == 0:
            returns = [ep["return"] for ep in completed_episodes_data]
            lengths = [ep["length"] for ep in completed_episodes_data]
            reasons = Counter(ep["reason"] for ep in completed_episodes_data)
            
            num_episodes = len(completed_episodes_data)
            avg_episode_return = sum(returns) / num_episodes if num_episodes > 0 else 0
            avg_episode_length = sum(lengths) / num_episodes if num_episodes > 0 else 0
            min_episode_return = min(returns) if num_episodes > 0 else 0
            max_episode_return = max(returns) if num_episodes > 0 else 0
            
            win_rate = reasons.get("bob_wins", 0) / num_episodes if num_episodes > 0 else 0
            avg_loss = sum(recent_losses) / len(recent_losses) if recent_losses else 0
            reasons_str = ", ".join(f"{k}={v}" for k, v in reasons.items())
            
            print(
                f"Episode {episode:5d} | DQN Loss: {avg_loss: 8.3f} | "
                f"Avg Episode Return: {avg_episode_return: 6.3f} | "
                f"Avg Episode Len: {avg_episode_length: 6.1f} | Episodes: {num_episodes:4d} | "
                f"WinRate (Bob): {win_rate: 6.2%} | Return[min/max]: {min_episode_return: 6.2f}/{max_episode_return: 6.2f} | "
                f"Reasons: {reasons_str}"
            )
            
            log_metrics_to_file(
                args.log_path, episode, num_episodes, win_rate, min_episode_return,
                avg_episode_return, max_episode_return, avg_episode_length,
                avg_loss, HEIGHT=HEIGHT, WIDTH=WIDTH, COLORS=COLORS
            )
            
            run_evaluation_episode(policy_net, eval_env)
            
            completed_episodes_data.clear()
            recent_losses.clear()
            
            if args.save_every > 0 and episode % args.save_every == 0:
                save_checkpoint(args.checkpoint_path, policy_net, optimizer, episode, config)
                print(f"Checkpoint saved: {args.checkpoint_path} (episode {episode})")

    save_checkpoint(args.checkpoint_path, policy_net, optimizer, episode, config)
    print(f"Final checkpoint saved: {args.checkpoint_path}")

if __name__ == "__main__":
    main()