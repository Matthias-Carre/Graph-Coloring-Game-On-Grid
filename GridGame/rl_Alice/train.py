import torch
import torch.optim as optim
import argparse
import os
from collections import Counter
from tensordict.nn import TensorDictModule
from torchrl.envs.libs.gym import GymWrapper
from torchrl.collectors import Collector # Updated from SyncDataCollector
from torchrl.objectives import ClipPPOLoss
from torchrl.objectives.value import GAE
from torchrl.modules import ProbabilisticActor, ValueOperator
from torchrl.modules.distributions import MaskedCategorical
from tensordict import TensorDict
import sys
from pathlib import Path

# Add parent directory to path to access game modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from ColoringEnv import GraphColoringEnv
from Model import GraphColoringNet


# Function to create 2D grid edges
def build_grid_edges(width, height):
    edges = []
    for y in range(height):
        for x in range(width):
            node = y * width + x
            if x > 0: edges.append([node, node - 1])
            if x < width - 1: edges.append([node, node + 1])
            if y > 0: edges.append([node, node - width])
            if y < height - 1: edges.append([node, node + width])
    return torch.tensor(edges, dtype=torch.long).t().contiguous()

def save_checkpoint(path, model, optimizer, batch_idx, config):
    checkpoint_dir = os.path.dirname(path)
    if checkpoint_dir:
        os.makedirs(checkpoint_dir, exist_ok=True)
    checkpoint = {
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "batch": batch_idx,
        "config": config,
    }
    torch.save(checkpoint, path)

def load_checkpoint(path, model, optimizer=None, device="cpu"):
    checkpoint = torch.load(path, map_location=device)
    model.load_state_dict(checkpoint["model_state_dict"])
    if optimizer is not None and "optimizer_state_dict" in checkpoint:
        optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
    return checkpoint

def log_metrics_to_file(log_path, batch_idx, num_episodes, win_rate, min_episode_return, 
                         avg_episode_return, max_episode_return, avg_episode_length,
                         actor_loss, value_loss, entropy_loss, HEIGHT, WIDTH, COLORS):
    """
    Logs training metrics to a CSV file for later analysis and plotting.
    """
    log_dir = os.path.dirname(log_path)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    
    # Write header if file doesn't exist
    file_exists = os.path.exists(log_path)
    
    with open(log_path, 'a') as f:
        if not file_exists or batch_idx == 0:
            f.write(f"Alice Training On size: w={WIDTH}, h={HEIGHT}, c={COLORS}\n")
            f.write("batch,num_episodes,win_rate,min_score,avg_score,max_score,avg_length,actor_loss,value_loss,entropy_loss\n")
            return
        if num_episodes > 0:
            f.write(f"{batch_idx},{num_episodes},{win_rate:.4f},{min_episode_return:.4f},{avg_episode_return:.4f},"
                    f"{max_episode_return:.4f},{avg_episode_length:.4f},{actor_loss:.6f},{value_loss:.6f},{entropy_loss:.6f}\n")

def run_evaluation_episode(policy, env):
    """
    Runs one evaluation episode and prints the final grid to give an idea of the game.
    """
    print("\n" + "="*30)
    print("EVALUATION: FINAL GRID")
    print("="*30)
    
    obs_dict, _ = env.reset()
    done = False
    total_reward = 0.0
    
    # Play the full episode without intermediate rendering
    while not done:
        # Convert observations to TensorDict format
        obs_tensor = torch.tensor(obs_dict["observation"], dtype=torch.float32).unsqueeze(0)
        mask_tensor = torch.tensor(obs_dict["mask"], dtype=torch.bool).unsqueeze(0)
        td = TensorDict({"observation": obs_tensor, "mask": mask_tensor}, batch_size=[1])
        
        # Query policy for the next action
        with torch.no_grad():
            result = policy(td)
            action = result["action"].item()
            
        # Step the environment
        obs_dict, reward, terminated, truncated, info = env.step(action)
        total_reward += reward
        done = terminated or truncated
        
    # Render only the final state
    env.render()
    print(f"End Reason: {info.get('reason', 'Unknown')} | Final Reward: {total_reward:.2f}")
    print("="*30 + "\n")

def backup_latest_checkpoint(checkpoint_path):
    if os.path.exists(checkpoint_path):
        backup_path = checkpoint_path.replace("latest.pt", "latest_backup.pt")
        torch.save(torch.load(checkpoint_path), backup_path)
        print(f"Backup of latest checkpoint saved to {backup_path}")

def main():
    # Set thread limit to prevent system freezing
    torch.set_num_threads(4)

    script_dir = Path(__file__).parent.parent
    default_checkpoint = str(script_dir / "checkpoints" / "Alice" / "latest.pt")
    default_log_file = str(script_dir / "checkpoints" / "Alice" / "training_metrics.csv")
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--checkpoint-path", type=str, default=default_checkpoint)
    parser.add_argument("--log-path", type=str, default=default_log_file)
    parser.add_argument("--save-every", type=int, default=500)
    args = parser.parse_args()

    WIDTH, HEIGHT, COLORS = 6, 6, 4
    LEARNING_RATE = 3e-4
    FRAMES_PER_BATCH = 200
    MINI_BATCH_SIZE = 125   # 4 mini-batches par batch, même mémoire
    PPO_EPOCHS = 4          # Réutilise chaque batch 4x = data efficiency x4
    TOTAL_FRAMES = 1_000_000
    GAMMA = 0.99
    
    backup_latest_checkpoint(args.checkpoint_path)

    print("Initializing environment...")    
    base_env = GraphColoringEnv(width=WIDTH, height=HEIGHT, num_colors=COLORS)
    env = GymWrapper(base_env, categorical_action_encoding=True)
    eval_env = GraphColoringEnv(width=WIDTH, height=HEIGHT, num_colors=COLORS)

    print("Creating Actor-Critic network...")
    core_network = GraphColoringNet(width=WIDTH, height=HEIGHT, num_colors=COLORS, hidden_dim=128, num_layers=3)
    
    # Static edge creation for the model
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    core_network = core_network.to(device)
    static_edge_index = build_grid_edges(WIDTH, HEIGHT).to(device)

    # Wrappers now accept edge_index
    class ActorWrapper(torch.nn.Module):
        def __init__(self, net, edge_index):
            super().__init__()
            self.net = net
            self.edge_index = edge_index
            
        def forward(self, obs, mask): 
            logits, _ = self.net(obs, self.edge_index)
            if obs.dim() == 3 and logits.dim() == 2:
                logits = logits.squeeze(0)
            if mask.dim() < logits.dim():
                mask = mask.unsqueeze(0).expand_as(logits)
            logits = logits.masked_fill(~mask.bool(), -1e8)
            return logits

    class CriticWrapper(torch.nn.Module):
        def __init__(self, net, edge_index):
            super().__init__()
            self.net = net
            self.edge_index = edge_index
            
        def forward(self, obs):
            _, value = self.net(obs, self.edge_index)
            if obs.dim() == 3 and value.dim() == 2:
                value = value.squeeze(0)
            return value
        
    actor_module = TensorDictModule(
        module=ActorWrapper(core_network, static_edge_index),
        in_keys=["observation", "mask"], 
        out_keys=["logits"]
    )
    
    policy = ProbabilisticActor(
        module=actor_module,
        in_keys=["logits", "mask"],
        out_keys=["action"],
        distribution_class=MaskedCategorical,
        return_log_prob=True
    )

    value_module = ValueOperator(
        module=CriticWrapper(core_network, static_edge_index),
        in_keys=["observation"],
        out_keys=["state_value"]
    )
    
    # Updated to Collector to avoid deprecation warnings
    collector = Collector(
        env, policy, frames_per_batch=FRAMES_PER_BATCH, total_frames=TOTAL_FRAMES, device="cpu" 
    )

    loss_module = ClipPPOLoss(
        actor_network=policy,
        critic_network=value_module,
        entropy_bonus=True,
        entropy_coef=0.03,  # Augmenté pour plus d'exploration
        clip_epsilon=0.2
    )
    loss_module.set_keys(advantage="advantage")

    advantage_module = GAE(gamma=GAMMA, lmbda=0.95, value_network=value_module, average_gae=True)
    optimizer = optim.Adam(core_network.parameters(), lr=LEARNING_RATE)

    config = {
        "width": WIDTH,
        "height": HEIGHT,
        "colors": COLORS,
        "learning_rate": LEARNING_RATE,
        "frames_per_batch": FRAMES_PER_BATCH,
        "total_frames": TOTAL_FRAMES,
        "gamma": GAMMA,
    }

    start_batch = 0
    if args.resume:
        if os.path.exists(args.checkpoint_path):
            checkpoint = load_checkpoint(args.checkpoint_path, core_network, optimizer, device="cpu")
            start_batch = int(checkpoint.get("batch", -1)) + 1
            print(f"Resumed from {args.checkpoint_path} at batch {start_batch}")
        else:
            print(f"Checkpoint not found at {args.checkpoint_path}. Starting fresh.")

    print("Starting PPO training loop...\n")
    for i, tensordict_data in enumerate(collector):
        batch_idx = start_batch + i 
        
        tensordict_data.set("action", tensordict_data.get("action").squeeze(-1))
        
        # Compute advantages without gradient tracking
        with torch.no_grad():
            tensordict_data = advantage_module(tensordict_data)

        # PPO: plusieurs passes sur les mêmes données avec mini-batches
        total_actor_loss, total_value_loss, total_entropy_loss = 0.0, 0.0, 0.0
        num_minibatches = 0

        for _ in range(PPO_EPOCHS):
            rand_idx = torch.randperm(FRAMES_PER_BATCH)
            shuffled_data = tensordict_data[rand_idx]

            for minibatch in shuffled_data.split(MINI_BATCH_SIZE):
                loss_dict = loss_module(minibatch)

                actor_loss = loss_dict["loss_objective"]
                value_loss = loss_dict["loss_critic"]
                entropy_loss = loss_dict["loss_entropy"]
                total_loss = actor_loss + value_loss + entropy_loss

                optimizer.zero_grad()
                total_loss.backward()
                torch.nn.utils.clip_grad_norm_(core_network.parameters(), max_norm=0.5)
                optimizer.step()

                total_actor_loss += actor_loss.item()
                total_value_loss += value_loss.item()
                total_entropy_loss += entropy_loss.item()
                num_minibatches += 1

        avg_actor_loss = total_actor_loss / num_minibatches
        avg_value_loss = total_value_loss / num_minibatches
        avg_entropy_loss = total_entropy_loss / num_minibatches

        # Logging metrics
        if batch_idx % 100 == 0:
            avg_reward = tensordict_data["next", "reward"].mean().item()

            completed_episodes = base_env.completed_episodes
            if completed_episodes:
                returns = [ep["return"] for ep in completed_episodes]
                lengths = [ep["length"] for ep in completed_episodes]
                reasons = Counter(ep["reason"] for ep in completed_episodes)

                num_episodes = len(completed_episodes)
                avg_episode_return = sum(returns) / len(returns)
                avg_episode_length = sum(lengths) / len(lengths)
                min_episode_return = min(returns)
                max_episode_return = max(returns)
                win_rate = reasons.get("alice_won", 0) / num_episodes
                reasons_str = ", ".join(f"{k}={v}" for k, v in reasons.items())
            else:
                num_episodes = 0
                avg_episode_return = float("nan")
                avg_episode_length = float("nan")
                min_episode_return = float("nan")
                max_episode_return = float("nan")
                win_rate = float("nan")
                reasons_str = "no completed episode in this batch"

            print(
                f"Batch {batch_idx:4d} | Actor Loss: {avg_actor_loss: 8.3f} | Value Loss: {avg_value_loss: 8.3f} | "
                f"Avg Step Reward: {avg_reward: 6.3f} | Avg Episode Return: {avg_episode_return: 6.3f} | "
                f"Avg Episode Len: {avg_episode_length: 6.1f} | Episodes: {num_episodes:4d} | "
                f"WinRate: {win_rate: 6.2%} | Return[min/max]: {min_episode_return: 6.2f}/{max_episode_return: 6.2f} | "
                f"Reasons: {reasons_str}"
            )

            base_env.completed_episodes.clear()
            
            # Log metrics to file
            log_metrics_to_file(
                args.log_path, batch_idx, num_episodes, win_rate, min_episode_return,
                avg_episode_return, max_episode_return, avg_episode_length,
                avg_actor_loss, avg_value_loss, avg_entropy_loss,
                HEIGHT=HEIGHT, WIDTH=WIDTH, COLORS=COLORS
            )

            run_evaluation_episode(policy, eval_env)

            if batch_idx > 0 and batch_idx % args.save_every == 0:
                save_checkpoint(args.checkpoint_path, core_network, optimizer, batch_idx, config)
                print(f"Checkpoint saved: {args.checkpoint_path} (batch {batch_idx})")

    # Final save
    save_checkpoint(args.checkpoint_path, core_network, optimizer, batch_idx, config)
    print(f"Final checkpoint saved: {args.checkpoint_path}")

if __name__ == "__main__":
    main()