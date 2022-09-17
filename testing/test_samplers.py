from typing import Literal

import pytest
import torch

from gfn.containers import ReplayBuffer, Trajectories
from gfn.envs import HyperGrid
from gfn.estimators import LogitPBEstimator, LogitPFEstimator
from gfn.samplers import TrajectoriesSampler, TransitionsSampler
from gfn.samplers.actions_samplers import (
    LogitPBActionsSampler,
    LogitPFActionsSampler,
)


@pytest.mark.parametrize("height", [4, 5])
@pytest.mark.parametrize("preprocessor_name", ["KHot", "OneHot", "Identity"])
def test_hypergrid_trajectory_sampling(
    height: int, preprocessor_name: str, human_print=False
) -> Trajectories:
    if human_print:
        print("---Trying Forward sampling of trajectories---")
    env = HyperGrid(ndim=2, height=height, preprocessor_name=preprocessor_name)

    if human_print:
        print("\nTrying the Fixed Actions Sampler: ")
    actions_sampler = LogitPFActionsSampler(
        LogitPFEstimator(env=env, module_name="NeuralNet")
    )
    trajectories_sampler = TrajectoriesSampler(env, actions_sampler)
    trajectories = trajectories_sampler.sample_trajectories(n_trajectories=5)
    if human_print:
        print(trajectories)

    if human_print:
        print("\nTrying the LogitPFActionSampler: ")

    logit_pf_estimator = LogitPFEstimator(env, module_name="NeuralNet")

    logit_pf_actions_sampler = LogitPFActionsSampler(estimator=logit_pf_estimator)

    trajectories_sampler = TrajectoriesSampler(env, logit_pf_actions_sampler)

    trajectories = trajectories_sampler.sample_trajectories(n_trajectories=10)
    if human_print:
        print(trajectories)

    if human_print:
        print("\n\n---Trying Backward sampling of trajectories---")

    states = env.reset(batch_shape=20, random_init=True)

    logit_pb_estimator = LogitPBEstimator(env=env, module_name="NeuralNet")

    logit_pb_actions_sampler = LogitPBActionsSampler(estimator=logit_pb_estimator)

    bw_trajectories_sampler = TrajectoriesSampler(env, logit_pb_actions_sampler)

    states = env.reset(batch_shape=5, random_init=True)
    bw_trajectories = bw_trajectories_sampler.sample_trajectories(states)
    if human_print:
        print(bw_trajectories)

    if human_print:
        print("\n\n---Making Sure Last states are computed correctly---")

    trajectories = trajectories_sampler.sample_trajectories(n_trajectories=5)
    if human_print:
        print(trajectories)
    return trajectories


@pytest.mark.parametrize("height", [4, 5])
def test_trajectories_getitem(height: int):
    trajectories = test_hypergrid_trajectory_sampling(height, preprocessor_name="KHot")
    print(f"There are {trajectories.n_trajectories} original trajectories")
    print(trajectories)
    print(trajectories[0])
    print(trajectories[[1, 0]])
    print(trajectories[torch.tensor([1, 2], dtype=torch.long)])


@pytest.mark.parametrize("height", [4, 5])
def test_trajectories_extend(height: int):
    trajectories = test_hypergrid_trajectory_sampling(height, preprocessor_name="KHot")
    print(
        f"There are {trajectories.n_trajectories} original trajectories. To which we will add the two first trajectories"
    )
    trajectories.extend(trajectories[[1, 0]])
    print(trajectories)


@pytest.mark.parametrize("height", [4, 5])
def test_sub_sampling(height: int):
    trajectories = test_hypergrid_trajectory_sampling(
        height, preprocessor_name="Identity"
    )
    print(
        f"There are {trajectories.n_trajectories} original trajectories, from which we will sample 2"
    )
    print(trajectories)
    sampled_trajectories = trajectories.sample(n_trajectories=2)
    print("The two sampled trajectories are:")
    print(sampled_trajectories)


@pytest.mark.parametrize("height", [4, 5])
def test_hypergrid_transition_sampling(height: int):
    env = HyperGrid(ndim=2, height=height)

    print("---Trying Forward sampling of trajectories---")

    print("Trying the Fixed Actions Sampler")
    actions_sampler = LogitPFActionsSampler(
        LogitPFEstimator(env=env, module_name="NeuralNet")
    )
    transitions_sampler = TransitionsSampler(env, actions_sampler)
    transitions = transitions_sampler.sample_transitions(n_transitions=5)
    print(transitions)

    transitions = transitions_sampler.sample_transitions(states=transitions.next_states)
    print(transitions)
    return transitions


@pytest.mark.parametrize("height", [4, 5])
@pytest.mark.parametrize("objects", ["trajectories", "transitions"])
def test_replay_buffer(height: int, objects: Literal["trajectories", "transitions"]):
    env = HyperGrid(ndim=2, height=height)
    replay_buffer = ReplayBuffer(env, capacity=10, objects=objects)
    print(f"After initialization, the replay buffer is {replay_buffer} ")
    if objects == "trajectories":
        training_objects = test_hypergrid_trajectory_sampling(
            height, preprocessor_name="Identity"
        )
        replay_buffer.add(
            training_objects[
                training_objects.when_is_done != training_objects.max_length
            ]
        )
    else:
        training_objects = test_hypergrid_transition_sampling(height)
        replay_buffer.add(training_objects)

    print(
        f"After adding {len(training_objects)} trajectories, the replay buffer is {replay_buffer} \n {replay_buffer.training_objects} "
    )
    replay_buffer.add(training_objects)
    print(
        f"After adding {len(training_objects)} trajectories, the replay buffer is {replay_buffer} \n {replay_buffer.training_objects}  "
    )
    replay_buffer.add(training_objects)
    print(
        f"After adding {len(training_objects)} trajectories, the replay buffer is {replay_buffer} \n {replay_buffer.training_objects}  "
    )
