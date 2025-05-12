import random

class QLearn:
    """
    Q-learning implementation for enemy AI.
    Q(s, a) += alpha * (reward(s,a) + gamma * max(Q(s', a') - Q(s,a))
    """
    def __init__(self, actions, alpha=0.1, gamma=0.9, epsilon=0.1):
        self.q = {}  # Q-table: (state, action) -> Q-value
        self.alpha = alpha  # Learning rate
        self.gamma = gamma  # Discount factor
        self.actions = actions  # List of possible actions
        self.epsilon = epsilon  # Exploration rate

    def get_utility(self, state, action):
        """Get Q-value for a state-action pair, default to 0.0."""
        return self.q.get((state, action), 0.0)

    def choose_action(self, state):
        """Choose an action using epsilon-greedy policy."""
        if random.random() < self.epsilon:
            action = random.choice(self.actions)
        else:
            q_values = [self.get_utility(state, act) for act in self.actions]
            max_q = max(q_values)
            if q_values.count(max_q) > 1:
                best_actions = [self.actions[i] for i in range(len(self.actions)) if q_values[i] == max_q]
                action = random.choice(best_actions)
            else:
                action = self.actions[q_values.index(max_q)]
        return action

    def learn(self, state1, action, state2, reward):
        """Update Q-value based on the Q-learning formula."""
        old_q = self.q.get((state1, action), 0.0)
        next_max_q = max([self.get_utility(state2, a) for a in self.actions])
        new_q = old_q + self.alpha * (reward + self.gamma * next_max_q - old_q)
        self.q[(state1, action)] = new_q