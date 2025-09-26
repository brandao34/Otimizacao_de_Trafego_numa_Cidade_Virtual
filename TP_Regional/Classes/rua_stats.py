



class Rua_Stats:
    def __init__(self, total_wait_time=0, total_reward=0.0, steps=0, current_time=0.0, vehicle_count=0, avg_speed=0.0, avg_wait_per_lane=0.0,  reward=0.0, done=False):
        self.total_wait_time = total_wait_time
        self.total_reward = total_reward
        self.steps = steps
        self.current_time = current_time
        self.vehicle_count = vehicle_count
        self.avg_speed = avg_speed
        self.avg_wait_per_lane = avg_wait_per_lane
        self.reward = reward 
        self.done = done  


    def to_dict(self):
        return {
            "total_wait_time": self.total_wait_time,
            "total_reward": self.total_reward,
            "steps": self.steps,
            "current_time": self.current_time,
            "vehicle_count": self.vehicle_count,
            "avg_speed": self.avg_speed,
            "avg_wait_per_lane": self.avg_wait_per_lane,
            "reward": self.reward,
            "done": self.done
        }