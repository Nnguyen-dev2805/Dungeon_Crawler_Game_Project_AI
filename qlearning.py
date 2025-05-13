import random

class QLearn:
    """
    Q(s, a) += alpha * (reward(s,a) + gamma * max(Q(s', a') - Q(s,a))
    """
    def __init__(self, actions, alpha=0.1, gamma=0.9, epsilon=0.1):
        self.q = {}   # lưu giá trị Q cho (trạng thái,hành động)
        self.alpha = alpha  
        self.gamma = gamma 
        self.actions = actions  
        self.epsilon = epsilon  

    def get_utility(self, state, action):
        # lấy giá trị của Q
        return self.q.get((state, action), 0.0)
    
    def choose_action(self, state, valid_actions):
        if not valid_actions: 
            return random.choice(self.actions)

        if random.random() < self.epsilon:
            action = random.choice(valid_actions)
        else:
            q_values = [self.get_utility(state, act) for act in self.actions]
            max_q = max([q for q, act in zip(q_values, self.actions) if act in valid_actions], default=0)
            best_actions = [act for act, q in zip(self.actions, q_values) if q == max_q and act in valid_actions]
            action = random.choice(best_actions) if best_actions else random.choice(valid_actions)
        return action
        
    # state 1 trạng thái hiện tại, state 2 trạng thái kế tiếp
    def learn(self, state1, action, state2, reward):
        old_q = self.q.get((state1, action), 0.0)
        next_max_q = max([self.get_utility(state2, a) for a in self.actions])
        new_q = old_q + self.alpha * (reward + self.gamma * next_max_q - old_q)
        self.q[(state1, action)] = new_q