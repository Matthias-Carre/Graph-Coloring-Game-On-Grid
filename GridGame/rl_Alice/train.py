import torch
import torch.optim as optim
import torch.nn as nn
from torch.distributions import Categorical
from ColoringEnv import GraphColoringEnv
from Model import GraphColoringNet

def train_ppo():
    # Setup environment and device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    env = GraphColoringEnv(width=5, height=5, num_colors=4)
    edge_index = env.edge_index.to(device)
    
    # Initialize the Graph Transformer
    model = GraphColoringNet(width=5, height=5, num_colors=4).to(device)
    optimizer = optim.Adam(model.parameters(), lr=3e-4)
    
    # Training hyperparameters
    num_episodes = 5000
    gamma = 0.99
    clip_epsilon = 0.2
    
    for episode in range(num_episodes):
        obs_dict, _ = env.reset()
        done = False
        
        log_probs_list = []
        values_list = []
        rewards_list = []
        
        # Phase 1: Collect trajectories
        while not done:
            obs = torch.tensor(obs_dict["observation"], dtype=torch.float32).to(device)
            mask = torch.tensor(obs_dict["mask"], dtype=torch.bool).to(device)
            
            # Forward pass
            logits, value = model(obs, edge_index, mask=mask)
            
            # Sample valid action using probabilities
            dist = Categorical(logits=logits)
            action = dist.sample()
            
            next_obs_dict, reward, terminated, truncated, info = env.step(action.item())
            done = terminated or truncated
            
            # Store transitions
            log_probs_list.append(dist.log_prob(action))
            values_list.append(value)
            rewards_list.append(reward)
            
            obs_dict = next_obs_dict
            
        # Phase 2: Compute Advantages (GAE simplified)
        returns = []
        R = 0
        for r in reversed(rewards_list):
            R = r + gamma * R
            returns.insert(0, R)
            
        returns = torch.tensor(returns, dtype=torch.float32).to(device)
        values = torch.cat(values_list).squeeze(-1)
        
        if values.dim() == 0:
            values = values.unsqueeze(0)
            
        advantages = returns - values.detach()
        
        # Phase 3: Optimize the policy
        log_probs = torch.stack(log_probs_list)
        
        # PPO Actor Loss (simplified without old_log_probs for clean loop)
        actor_loss = -(log_probs * advantages).mean()
        
        # Critic Loss (MSE)
        critic_loss = nn.MSELoss()(values, returns)
        
        # Total loss
        total_loss = actor_loss + 0.5 * critic_loss
        
        # Update network weights
        optimizer.zero_grad()
        total_loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=0.5)
        optimizer.step()
        
        if episode % 50 == 0:
            print(f"Episode {episode:4d} | Reward: {sum(rewards_list):5.1f} | Reason: {info.get('reason')}")

if __name__ == "__main__":
    print("Starting Graph Transformer PPO Training...")
    train_ppo()