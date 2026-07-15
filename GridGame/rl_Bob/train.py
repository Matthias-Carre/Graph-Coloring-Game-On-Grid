import torch
import torch.optim as optim
import torch.nn.functional as F
from torch.distributions import Categorical
from torch_geometric.data import Data, Batch
import argparse
import os
import sys
from pathlib import Path
from collections import Counter
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from Model import GraphColoringTransformerPPO 
from ColoringEnv import ColoringEnv

def save_checkpoint(path, model, optimizer, update_idx, config):
    # Serializes neural network state to disk
    checkpoint_dir = os.path.dirname(path)
    if checkpoint_dir:
        os.makedirs(checkpoint_dir, exist_ok=True)
    checkpoint = {
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "update": update_idx,
        "config": config,
    }
    torch.save(checkpoint, path)

def load_checkpoint(path, model, optimizer=None, device="cpu"):
    # Reconstructs model state from file
    checkpoint = torch.load(path, map_location=device)
    model.load_state_dict(checkpoint["model_state_dict"])
    if optimizer is not None and "optimizer_state_dict" in checkpoint:
        optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
    return checkpoint

def log_metrics_to_file(log_path, update_idx, total_episodes, win_rate, min_return, 
                         avg_return, max_return, avg_length, ppo_loss, HEIGHT, WIDTH, COLORS):
    # Appends training progression to CSV
    log_dir = os.path.dirname(log_path)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    
    file_exists = os.path.exists(log_path)
    
    with open(log_path, 'a') as f:
        if not file_exists or update_idx == 1:
            f.write(f"Bob PPO Transformer Training On size: w={WIDTH}, h={HEIGHT}, c={COLORS}\n")
            f.write("update,total_episodes,win_rate,min_score,avg_score,max_score,avg_length,ppo_loss\n")
        if total_episodes > 0:
            f.write(f"{update_idx},{total_episodes},{win_rate:.4f},{min_return:.4f},{avg_return:.4f},"
                f"{max_return:.4f},{avg_length:.4f},{ppo_loss:.6f}\n")

def run_evaluation_episode(policy_net, env):
    # Runs greedy policy to visualize current performance
    print("\n" + "="*30)
    print("EVALUATION: FINAL GRID")
    print("="*30)
    
    state = env.reset()
    done = False
    total_reward = 0.0
    reason = "Unknown"
    
    while not done:
        mask = state["mask"]
        valid_actions = torch.where(mask)[0]
        
        if len(valid_actions) == 0:
            reason = "No valid moves"
            break
            
        with torch.no_grad():
            # Inject spatial parameters into the transformer
            logits, _ = policy_net(state["x"], state["edge_index"], state["edge_attr"], batch_size=1)
            masked_logits = logits[0].masked_fill(~mask, float('-inf'))
            action = masked_logits.argmax().item()
            
        state, reward, done = env.step(action)
        total_reward += reward
        
        if done:
            if reward >= 10.0:
                reason = "bob_wins"
            else:
                reason = "alice_wins / grid_full"
        
    env.render()
    print(f"End Reason: {reason} | Final Reward: {total_reward:.2f}")
    print("="*30 + "\n")

def compute_gae(rewards, values, dones, gamma, lam):
    # Calculates Generalized Advantage Estimation for variance reduction
    advantages = []
    last_advantage = 0
    for t in reversed(range(len(rewards))):
        mask = 1.0 - dones[t]
        next_value = values[t+1] if t + 1 < len(values) else 0.0
        delta = rewards[t] + gamma * next_value * mask - values[t]
        last_advantage = delta + gamma * lam * mask * last_advantage
        advantages.insert(0, last_advantage)
    return advantages

def main():
    script_dir = Path(__file__).parent.parent 
    default_checkpoint = str(script_dir / "checkpoints" / "Bob_PPO" / "latest.pt")
    default_log_file = str(script_dir / "checkpoints" / "Bob_PPO" / "training_metrics.csv")
    
    parser = argparse.ArgumentParser(description="Train Graph Transformer PPO agent.")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint.")
    parser.add_argument("--checkpoint-path", type=str, default=default_checkpoint, help="Path to checkpoint file.")
    parser.add_argument("--log-path", type=str, default=default_log_file, help="Path to metrics log file.")
    parser.add_argument("--save-every", type=int, default=50, help="Save checkpoint every N updates.")
    args = parser.parse_args()

    # Transformer & PPO Constants
    WIDTH, HEIGHT, COLORS = 5, 5, 4
    LEARNING_RATE = 3e-4
    GAMMA = 0.99
    GAE_LAMBDA = 0.95
    CLIP_EPSILON = 0.2
    ENTROPY_COEF = 0.01
    VALUE_COEF = 0.5
    
    STEPS_PER_UPDATE = 1024
    PPO_EPOCHS = 4
    TOTAL_UPDATES = 1000
    
    print("Initializing environment...")
    env = ColoringEnv(width=WIDTH, height=HEIGHT, num_colors=COLORS)
    eval_env = ColoringEnv(width=WIDTH, height=HEIGHT, num_colors=COLORS)

    print("Creating Graph Transformer PPO network...")
    num_node_features = (COLORS + 1) + 2
    policy_net = GraphColoringTransformerPPO(num_node_features, hidden_size=64, num_colors=COLORS)
    optimizer = optim.Adam(policy_net.parameters(), lr=LEARNING_RATE)

    config = {
        "width": WIDTH, "height": HEIGHT, "colors": COLORS,
        "learning_rate": LEARNING_RATE, "gamma": GAMMA, "clip": CLIP_EPSILON
    }

    start_update = 1
    total_episodes_counter = 0
    if args.resume and os.path.exists(args.checkpoint_path):
        checkpoint = load_checkpoint(args.checkpoint_path, policy_net, optimizer)
        start_update = int(checkpoint.get("update", 0)) + 1
        print(f"Resumed from {args.checkpoint_path} at update {start_update}")

    print("Starting PPO training loop...\n")
    
    for update in range(start_update, TOTAL_UPDATES + 1):
        batch_states = []
        batch_actions = []
        batch_log_probs = []
        batch_rewards = []
        batch_values = []
        batch_dones = []
        
        completed_episodes_data = []
        state = env.reset()
        episode_reward = 0
        episode_length = 0
        
        # 1. Rollout Phase
        for step in range(STEPS_PER_UPDATE):
            mask = state["mask"]
            valid_actions = torch.where(mask)[0]
            
            if len(valid_actions) == 0:
                completed_episodes_data.append({"return": episode_reward, "length": episode_length, "reason": "no_valid_moves"})
                state = env.reset()
                episode_reward = 0
                episode_length = 0
                continue
                
            with torch.no_grad():
                logits, value = policy_net(state["x"], state["edge_index"], state["edge_attr"], batch_size=1)
                masked_logits = logits[0].masked_fill(~mask, float('-inf'))
                
                probs = F.softmax(masked_logits, dim=-1)
                dist = Categorical(probs)
                action = dist.sample()
                log_prob = dist.log_prob(action)
            
            next_state, reward, done = env.step(action.item())
            
            batch_states.append((state, mask))
            batch_actions.append(action)
            batch_log_probs.append(log_prob)
            batch_rewards.append(reward)
            batch_values.append(value.item())
            batch_dones.append(done)
            
            episode_reward += reward
            episode_length += 1
            state = next_state
            
            if done:
                if reward >= 10.0:
                    reason = "bob_wins"
                elif reward <= -10.0:
                    reason = "bob_loses"
                else:
                    reason = "timeout"
                    
                completed_episodes_data.append({"return": episode_reward, "length": episode_length, "reason": reason})
                total_episodes_counter += 1
                state = env.reset()
                episode_reward = 0
                episode_length = 0

        # 2. Compute Advantage Array
        with torch.no_grad():
            _, next_value = policy_net(state["x"], state["edge_index"], state["edge_attr"], batch_size=1)
            batch_values.append(next_value.item())
            
        advantages = compute_gae(batch_rewards, batch_values, batch_dones, GAMMA, GAE_LAMBDA)
        advantages = torch.tensor(advantages, dtype=torch.float32)
        returns = advantages + torch.tensor(batch_values[:-1], dtype=torch.float32)
        
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
        
        b_actions = torch.stack(batch_actions)
        b_log_probs = torch.stack(batch_log_probs)
        
        # 3. Optimization Phase
        total_loss = 0
        for epoch in range(PPO_EPOCHS):
            # Form graph batch integrating local topologies and global spatial distances
            states_list = [Data(x=s[0]["x"], edge_index=s[0]["edge_index"], edge_attr=s[0]["edge_attr"]) for s in batch_states]
            b_masks = torch.stack([s[1] for s in batch_states])
            batched_states = Batch.from_data_list(states_list)
            
            logits, values = policy_net(batched_states.x, batched_states.edge_index, batched_states.edge_attr, batch_index=batched_states.batch, batch_size=len(batch_states))
            values = values.squeeze()
            
            masked_logits = logits.masked_fill(~b_masks, float('-inf'))
            probs = F.softmax(masked_logits, dim=-1)
            dist = Categorical(probs)
            
            new_log_probs = dist.log_prob(b_actions)
            entropy = dist.entropy().mean()
            
            ratio = torch.exp(new_log_probs - b_log_probs)
            surr1 = ratio * advantages
            surr2 = torch.clamp(ratio, 1.0 - CLIP_EPSILON, 1.0 + CLIP_EPSILON) * advantages
            actor_loss = -torch.min(surr1, surr2).mean()
            
            critic_loss = F.mse_loss(values, returns)
            
            loss = actor_loss + VALUE_COEF * critic_loss - ENTROPY_COEF * entropy
            
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(policy_net.parameters(), max_norm=0.5)
            optimizer.step()
            
            total_loss += loss.item()
            
        avg_loss = total_loss / PPO_EPOCHS
        
        # 4. Metrics Reporting
        if len(completed_episodes_data) > 0:
            returns_data = [ep["return"] for ep in completed_episodes_data]
            lengths = [ep["length"] for ep in completed_episodes_data]
            reasons = Counter(ep["reason"] for ep in completed_episodes_data)
            
            num_episodes = len(completed_episodes_data)
            avg_return = sum(returns_data) / num_episodes
            avg_len = sum(lengths) / num_episodes
            min_ret, max_ret = min(returns_data), max(returns_data)
            win_rate = reasons.get("bob_wins", 0) / num_episodes
            
            reasons_str = ", ".join(f"{k}={v}" for k, v in reasons.items())
            print(f"Update {update:4d} | Loss: {avg_loss: 6.3f} | Episodes: {num_episodes:3d} | "
                  f"WinRate: {win_rate: 6.2%} | AvgReturn: {avg_return: 6.2f} | "
                  f"Reasons: {reasons_str}")
                  
            log_metrics_to_file(args.log_path, update, total_episodes_counter, win_rate, min_ret, 
                                avg_return, max_ret, avg_len, avg_loss, HEIGHT, WIDTH, COLORS)
                                
        if args.save_every > 0 and update % args.save_every == 0:
            save_checkpoint(args.checkpoint_path, policy_net, optimizer, update, config)
            run_evaluation_episode(policy_net, eval_env)

    print(f"Final checkpoint saved: {args.checkpoint_path}")

if __name__ == "__main__":
    main()