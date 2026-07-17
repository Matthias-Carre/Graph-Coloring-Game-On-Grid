import torch
import torch.optim as optim
import argparse
import os
import warnings
from collections import Counter
from tensordict.nn import TensorDictModule
from torchrl.envs.libs.gym import GymWrapper
from torchrl.collectors import SyncDataCollector

# PPO imports
from torchrl.objectives import ClipPPOLoss
from torchrl.objectives.value import GAE
from torchrl.modules import ProbabilisticActor, ValueOperator
from torchrl.modules.distributions import MaskedCategorical

from tensordict import TensorDict
import sys
from pathlib import Path

# ==========================================
# Suppress TorchRL/PyTorch internal warnings
# ==========================================
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)

sys.path.insert(0, str(Path(__file__).parent.parent))

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
                         actor_loss, value_loss, entropy_loss, HEIGHT, WIDTH, COLORS):
    log_dir = os.path.dirname(log_path)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    
    file_exists = os.path.exists(log_path)
    with open(log_path, 'a') as f:
        if not file_exists or batch_idx == 0:
            f.write(f"Bob PPO Training On size: w={WIDTH}, h={HEIGHT}, c={COLORS}\n")
            f.write("batch,num_episodes,win_rate,min_score,avg_score,max_score,avg_length,actor_loss,value_loss,entropy_loss\n")
        if num_episodes > 0:
            f.write(f"{batch_idx},{num_episodes},{win_rate:.4f},{min_episode_return:.4f},{avg_episode_return:.4f},"
                f"{max_episode_return:.4f},{avg_episode_length:.4f},{actor_loss:.6f},{value_loss:.6f},{entropy_loss:.6f}\n")

def run_evaluation_episode(policy, env):
    print("\n" + "="*30)
    print("EVALUATION: FINAL GRID")
    print("="*30)
    
    obs_dict, _ = env.reset()
    done = False
    total_reward = 0.0
    
    while not done:
        obs_tensor = torch.tensor(obs_dict["observation"], dtype=torch.float32).unsqueeze(0)
        mask_tensor = torch.tensor(obs_dict["mask"], dtype=torch.bool).unsqueeze(0)
        td = TensorDict({"observation": obs_tensor, "mask": mask_tensor}, batch_size=[1])
        
        with torch.no_grad():
            result = policy(td)
            action = result["action"].item()
            
        obs_dict, reward, terminated, truncated, info = env.step(action)
        total_reward += reward
        done = terminated or truncated
        
    env.render()
    print(f"End Reason: {info.get('reason', 'Unknown')} | Final Reward: {total_reward:.2f}")
    print("="*30 + "\n")

def main():
    script_dir = Path(__file__).parent.parent 
    default_checkpoint = str(script_dir / "checkpoints"/ "Bob" / "latest.pt")
    default_log_file = str(script_dir / "checkpoints" / "Bob" / "training_metrics.csv")
    
    parser = argparse.ArgumentParser(description="Train Graph Transformer PPO agent.")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint.")
    parser.add_argument("--checkpoint-path", type=str, default=default_checkpoint, help="Path to checkpoint file.")
    parser.add_argument("--log-path", type=str, default=default_log_file, help="Path to training metrics log file.")
    parser.add_argument("--save-every", type=int, default=100, help="Save checkpoint every N batches.")
    args = parser.parse_args()

    # ==========================================
    # MEMORY OPTIMIZED PPO HYPERPARAMETERS
    # ==========================================
    WIDTH, HEIGHT, COLORS = 6, 6, 4
    LEARNING_RATE = 3e-4
    FRAMES_PER_BATCH = 256     # Reduced to prevent advantage_module OOM
    MINI_BATCH_SIZE = 64       # Chunk size to prevent PPO backward OOM
    TOTAL_FRAMES = 512_000     # Adjusted to be a perfect multiple of 256
    GAMMA = 0.99
    PPO_EPOCHS = 4
    
    print("Initializing environment...")
    base_env = GraphColoringEnv(width=WIDTH, height=HEIGHT, num_colors=COLORS)
    env = GymWrapper(base_env, categorical_action_encoding=True)
    eval_env = GraphColoringEnv(width=WIDTH, height=HEIGHT, num_colors=COLORS)

    print("Creating Graph Transformer Actor-Critic network...")
    core_network = GraphColoringNet(width=WIDTH, height=HEIGHT, num_colors=COLORS)

    class ActorWrapper(torch.nn.Module):
        def __init__(self, net):
            super().__init__()
            self.net = net
            
        def forward(self, obs, mask): 
            logits, _ = self.net(obs)
            if obs.dim() == 3 and logits.dim() == 2:
                logits = logits.squeeze(0)
            if mask.dim() < logits.dim():
                mask = mask.unsqueeze(0).expand_as(logits)
            logits = logits.masked_fill(~mask.bool(), -1e8)
            return logits

    class CriticWrapper(torch.nn.Module):
        def __init__(self, net):
            super().__init__()
            self.net = net
            
        def forward(self, obs):
            _, value = self.net(obs)
            if obs.dim() == 3 and value.dim() == 2:
                value = value.squeeze(0)
            return value
        
    actor_module = TensorDictModule(
        module=ActorWrapper(core_network),
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
        module=CriticWrapper(core_network),
        in_keys=["observation"],
        out_keys=["state_value"]
    )
    
    print("Setting up SyncDataCollector...")
    collector = SyncDataCollector(
        env,
        policy,
        frames_per_batch=FRAMES_PER_BATCH,
        total_frames=TOTAL_FRAMES,
        device="cpu" 
    )

    loss_module = ClipPPOLoss(
        actor_network=policy,
        critic_network=value_module,
        entropy_bonus=True,
        entropy_coef=0.01,
        clip_epsilon=0.2
    )

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
        "mini_batch_size": MINI_BATCH_SIZE,
        "total_frames": TOTAL_FRAMES,
        "gamma": GAMMA,
        "ppo_epochs": PPO_EPOCHS
    }

    start_batch = 0
    if args.resume and os.path.exists(args.checkpoint_path):
        checkpoint = load_checkpoint(args.checkpoint_path, core_network, optimizer, device="cpu")
        start_batch = int(checkpoint.get("batch", -1)) + 1
        print(f"Resumed from {args.checkpoint_path} at batch {start_batch}")

    print("Starting PPO training loop...\n")
    for i, tensordict_data in enumerate(collector):
        batch_idx = start_batch + i
        
        tensordict_data.set("action", tensordict_data.get("action").squeeze(-1))
        
        with torch.no_grad():
            # Advantage computation on 256 frames (Safe for RAM)
            tensordict_data = advantage_module(tensordict_data)

        # ==========================================
        # MINI-BATCH OPTIMIZATION PHASE
        # ==========================================
        total_actor_loss, total_value_loss, total_entropy = 0, 0, 0
        num_minibatches = 0
        
        for _ in range(PPO_EPOCHS):
            # Shuffle the full batch
            rand_idx = torch.randperm(FRAMES_PER_BATCH)
            shuffled_data = tensordict_data[rand_idx]
            
            # Process in chunks of 64 to prevent RAM explosion during backward pass
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
                total_entropy += entropy_loss.item()
                num_minibatches += 1

        # Calculate averages across all minibatches
        avg_actor_loss = total_actor_loss / num_minibatches
        avg_value_loss = total_value_loss / num_minibatches
        avg_entropy_loss = total_entropy / num_minibatches

        # Metrics reporting
        if batch_idx % 10 == 0:
            avg_reward = tensordict_data["next", "reward"].mean().item()
            completed_episodes = base_env.completed_episodes
            
            if completed_episodes:
                returns = [ep["return"] for ep in completed_episodes]
                lengths = [ep["length"] for ep in completed_episodes]
                reasons = Counter(ep["reason"] for ep in completed_episodes)

                num_episodes = len(completed_episodes)
                avg_episode_return = sum(returns) / num_episodes
                avg_episode_length = sum(lengths) / num_episodes
                min_episode_return, max_episode_return = min(returns), max(returns)
                win_rate = (num_episodes - reasons.get("bob_loses", 0)) / num_episodes
                reasons_str = ", ".join(f"{k}={v}" for k, v in reasons.items())
            else:
                num_episodes, win_rate = 0, float("nan")
                avg_episode_return, avg_episode_length = float("nan"), float("nan")
                min_episode_return, max_episode_return = float("nan"), float("nan")
                reasons_str = "no completed episode"

            print(
                f"Update {batch_idx:4d} | ALoss: {avg_actor_loss: 6.3f} | VLoss: {avg_value_loss: 6.3f} | "
                f"Avg Reward: {avg_reward: 6.3f} | Avg Return: {avg_episode_return: 6.3f} | "
                f"WinRate: {win_rate: 6.2%} | Reasons: {reasons_str}"
            )

            base_env.completed_episodes.clear()
            log_metrics_to_file(
                args.log_path, batch_idx, num_episodes, win_rate, min_episode_return,
                avg_episode_return, max_episode_return, avg_episode_length,
                avg_actor_loss, avg_value_loss, avg_entropy_loss,
                HEIGHT=HEIGHT, WIDTH=WIDTH, COLORS=COLORS
            )

            if args.save_every > 0 and batch_idx > 0 and batch_idx % args.save_every == 0:
                run_evaluation_episode(policy, eval_env)
                save_checkpoint(args.checkpoint_path, core_network, optimizer, batch_idx, config)

    save_checkpoint(args.checkpoint_path, core_network, optimizer, batch_idx, config)
    print(f"Final checkpoint saved: {args.checkpoint_path}")

if __name__ == "__main__":
    main()