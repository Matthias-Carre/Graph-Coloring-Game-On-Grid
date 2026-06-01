import torch
import torch.optim as optim
import argparse
import os
from collections import Counter
from tensordict.nn import TensorDictModule
from torchrl.envs.libs.gym import GymWrapper
from torchrl.collectors import SyncDataCollector

#from torchrl.objectives import ReinforceLoss
from torchrl.objectives import A2CLoss

from torchrl.objectives.value import GAE
from torchrl.modules import ProbabilisticActor, ValueOperator
from torchrl.modules.distributions import MaskedCategorical

from tensordict import TensorDict
import sys
from pathlib import Path

# Add parent directory to path to access game modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import custom environment and model.
from ColoringEnv import GraphColoringEnv
from Model import GraphColoringNet


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
                         actor_loss, value_loss, entropy_loss):
    """
    Logs training metrics to a CSV file for later analysis and plotting.
    """
    log_dir = os.path.dirname(log_path)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    
    # Write header if file doesn't exist
    file_exists = os.path.exists(log_path)
    
    with open(log_path, 'a') as f:
        if not file_exists:
            f.write("batch,num_episodes,win_rate,min_score,avg_score,max_score,avg_length,actor_loss,value_loss,entropy_loss\n")
        f.write(f"{batch_idx},{num_episodes},{win_rate:.4f},{min_episode_return:.4f},{avg_episode_return:.4f},"
                f"{max_episode_return:.4f},{avg_episode_length:.4f},{actor_loss:.6f},{value_loss:.6f},{entropy_loss:.6f}\n")

def run_evaluation_episode(policy, env):
    """
    Runs one evaluation episode print the final gird to give an idea of the game
    """
    print("\n" + "="*30)
    print("EVALUATION: FINAL GRID")
    print("="*30)
    
    obs_dict, _ = env.reset()
    done = False
    total_reward = 0.0
    
    # Play the full episode without intermediate rendering.
    while not done:
        # Convert observations to TensorDict format.
        obs_tensor = torch.tensor(obs_dict["observation"], dtype=torch.float32).unsqueeze(0)
        mask_tensor = torch.tensor(obs_dict["mask"], dtype=torch.bool).unsqueeze(0)
        td = TensorDict({"observation": obs_tensor, "mask": mask_tensor}, batch_size=[1])
        
        # Query policy for the next action.
        with torch.no_grad():
            result = policy(td)
            action = result["action"].item()
            
        # Step the environment.
        obs_dict, reward, terminated, truncated, info = env.step(action)
        total_reward += reward
        done = terminated or truncated
        
    # Render only the final state.
    env.render()
    print(f"End Reason: {info.get('reason', 'Unknown')} | Final Reward: {total_reward:.2f}")
    print("="*30 + "\n")



def main():
    # Calculate checkpoint path relative to this script location
    script_dir = Path(__file__).parent.parent  # GridGame directory
    default_checkpoint = str(script_dir / "checkpoints" / "Alice" / "latest.pt")
    default_log_file = str(script_dir / "checkpoints" / "Alice" / "training_metrics.csv")
    
    parser = argparse.ArgumentParser(description="Train graph coloring agent.")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint.")
    parser.add_argument(
        "--checkpoint-path",
        type=str,
        default=default_checkpoint,
        help="Path to checkpoint file.",
    )
    parser.add_argument(
        "--log-path",
        type=str,
        default=default_log_file,
        help="Path to training metrics log file.",
    )
    parser.add_argument(
        "--save-every",
        type=int,
        default=500,
        help="Save checkpoint every N batches.",
    )
    args = parser.parse_args()

    # Hyperparameters.
    WIDTH, HEIGHT, COLORS = 8, 8, 4
    LEARNING_RATE = 1e-3
    FRAMES_PER_BATCH = 100    # Steps collected before updating the network
    TOTAL_FRAMES = 500_000     # Total training steps
    GAMMA = 0.99              # Discount factor for future rewards
    


    # Environment setup.
    print("Initializing environment...")
    base_env = GraphColoringEnv(width=WIDTH, height=HEIGHT, num_colors=COLORS)
    # Convert Gymnasium outputs to TensorDict for TorchRL.
    env = GymWrapper(base_env, categorical_action_encoding=True)

    eval_env = GraphColoringEnv(width=WIDTH, height=HEIGHT, num_colors=COLORS)

        # Neural network setup.
    print("Creating Actor-Critic network...")
    core_network = GraphColoringNet(width=WIDTH, height=HEIGHT, num_colors=COLORS)

    # Wrappers to split actor and critic outputs.
    class ActorWrapper(torch.nn.Module):
        def __init__(self, net):
            super().__init__()
            self.net = net
            
        def forward(self, obs, mask): 
            logits, _ = self.net(obs)
            
            # Handle the case where the model creates an artificial batch dimension.
            if obs.dim() == 3 and logits.dim() == 2:
                logits = logits.squeeze(0)  # [1, A] -> [A]
                
                
            # Align mask shape with logits when needed.
            if mask.dim() < logits.dim():
                mask = mask.unsqueeze(0).expand_as(logits)

            # Set illegal actions to a very negative value.
            logits = logits.masked_fill(~mask.bool(), -1e8)
            return logits

    class CriticWrapper(torch.nn.Module):
        def __init__(self, net):
            super().__init__()
            self.net = net
            
        def forward(self, obs):
            _, value = self.net(obs)
            
            # Apply the same batch-dimension guard for value output.
            if obs.dim() == 3 and value.dim() == 2:
                value = value.squeeze(0)
                
            return value
        

        
    # Actor module: takes observation and action mask.
    actor_module = TensorDictModule(
        module=ActorWrapper(core_network),
        in_keys=["observation", "mask"], 
        out_keys=["logits"]
    )
    
    # Probabilistic actor: samples actions from masked logits.
    policy = ProbabilisticActor(
        module=actor_module,
        in_keys=["logits", "mask"],
        out_keys=["action"],
        distribution_class=MaskedCategorical,
        return_log_prob=True
    )

    # Critic module: estimates state value from observation.
    value_module = ValueOperator(
        module=CriticWrapper(core_network),
        in_keys=["observation"],
        out_keys=["state_value"]
    )

    
    # Data collector.
    print("Setting up SyncDataCollector...")
    collector = SyncDataCollector(
        env,
        policy,
        frames_per_batch=FRAMES_PER_BATCH,
        total_frames=TOTAL_FRAMES,
        device="cpu" 
    )


    # Loss and advantage modules.
    # A2C objective with entropy regularization.
    loss_module = A2CLoss(
        actor_network=policy,
        critic_network=value_module,
        entropy_bonus=True,
        entropy_coef=0.05
    )
    loss_module.set_keys(advantage="advantage")

    # Generalized Advantage Estimation (Gt - V(s)).
    advantage_module = GAE(
        gamma=GAMMA,
        lmbda=0.95,
        value_network=value_module,
        average_gae=True
    )

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

    # Training loop.
    print("Starting training loop...\n")
    for i, tensordict_data in enumerate(collector):
        batch_idx = start_batch + i
        
        tensordict_data.set("action", tensordict_data.get("action").squeeze(-1))
        # Compute advantages without gradient tracking.
        with torch.no_grad():
            tensordict_data = advantage_module(tensordict_data)

        # Compute A2C losses.
        loss_dict = loss_module(tensordict_data)
        
        # Extract loss components.
        actor_loss = loss_dict["loss_objective"]
        value_loss = loss_dict["loss_critic"]
        entropy_loss = loss_dict["loss_entropy"]  # Optional, useful for monitoring.
        
        # Build total optimization loss.
        total_loss = actor_loss + value_loss + entropy_loss

        # Backpropagation.
        optimizer.zero_grad()
        total_loss.backward()
        optimizer.step()

        # Logging metrics.
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
                f"Batch {batch_idx:4d} | Actor Loss: {actor_loss.item(): 8.3f} | Value Loss: {value_loss.item(): 8.3f} | "
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
                actor_loss.item(), value_loss.item(), entropy_loss.item()
            )

            run_evaluation_episode(policy, eval_env)

            if args.save_every > 0 and batch_idx > 0 and batch_idx % args.save_every == 0:
                save_checkpoint(args.checkpoint_path, core_network, optimizer, batch_idx, config)
                print(f"Checkpoint saved: {args.checkpoint_path} (batch {batch_idx})")

    save_checkpoint(args.checkpoint_path, core_network, optimizer, batch_idx, config)
    print(f"Final checkpoint saved: {args.checkpoint_path}")


if __name__ == "__main__":
    main()