from math import ceil, floor, sqrt
from sam3x_helper import uint32_t, int32_t, uint, int_
import config


class Block():
    pass

current_block = Block()

block = [current_block]

current_block.nominal_rate = config.SPEED_MM_S * config.STEPS_PER_MM  # mm/s * steps/mm
current_block.initial_rate = 0  # changes in planner (jerk etc.)
current_block.acceleration_st = ceil(config.ACCELERATION * config.STEPS_PER_MM)

current_block.millimeters = config.TRAVEL_IN_MM  # mm to travel
current_block.step_event_count = current_block.millimeters * config.STEPS_PER_MM

current_block.acceleration_rate = int32_t(current_block.acceleration_st * (2**24) / config.HAL_TIMER_RATE)
current_block.acceleration = current_block.acceleration_st / config.STEPS_PER_MM

print("{}:{}".format(config.ACCELERATION, current_block.acceleration_rate))


def estimate_acceleration_distance(initial_rate, target_rate, acceleration):
    if acceleration != 0:
        return ((target_rate ** 2 - initial_rate ** 2)
                / (2.0 * acceleration))
    else:
        return 0.0


def intersection_distance(initial_rate, final_rate, acceleration, distance):
    if acceleration != 0:
        return ((2.0 * acceleration * distance - initial_rate ** 2 + final_rate ** 2)
                / (4.0 * acceleration))
    else:
        return 0.0


def calculate_trapezoid_for_block(block, entry_factor, exit_factor):
    # global current_block
    # current_block = block[myblock]

    initial_rate = uint32_t(ceil(block.nominal_rate * entry_factor))
    final_rate = uint32_t(ceil(block.nominal_rate * exit_factor))

    LIMIT = 120
    if initial_rate < LIMIT:
        initial_rate = LIMIT
    if final_rate < LIMIT:
        final_rate = LIMIT

    acceleration = int32_t(block.acceleration_st)
    acceleration_steps = int32_t(ceil(estimate_acceleration_distance(
        initial_rate,
        block.nominal_rate,
        acceleration)))
    decelerate_steps = int32_t(floor(estimate_acceleration_distance(
        block.nominal_rate,
        final_rate,
        -acceleration)))

    plateau_steps = int32_t(block.step_event_count - acceleration_steps - decelerate_steps)

    if plateau_steps < 0:
        acceleration_steps = ceil(intersection_distance(
            initial_rate,
            final_rate,
            acceleration,
            block.step_event_count))
        acceleration_steps = max(acceleration_steps, 0)
        acceleration_steps = min(uint32_t(acceleration_steps),
                                 block.step_event_count)
        plateau_steps = 0

    block.accelerate_until = int32_t(acceleration_steps)
    block.decelerate_after = int32_t(acceleration_steps + plateau_steps)
    block.initial_rate = initial_rate
    block.final_rate = final_rate

    print("---- from planner --------")
    print("acc_until: {0}".format(block.accelerate_until))
    print("dec_after: {0}".format(block.decelerate_after))
    print("--------------------------")

    return block


def max_allowable_speed(acceleration, target_velocity, distance):
    return sqrt(target_velocity**2 - 2*acceleration*distance)


def planner_reverse_pass_kernel(previous_block, current_block, next_block):
    if current_block.entry_speed != current_block.max_entry_speed:

        if not current_block.nominal_length_flag and current_block.max_entry_speed > next_block.entry_speed:
            current_block.entry_speed = min(current_block.max_entry_speed,
                                            max_allowable_speed(-current_block.acceleration,
                                                                next_block.entry_speed,
                                                                current_block.millimeters))
        else:
            current_block.entry_speed = current_block.max_entry_speed

        current_block.recalculate_flag = True


# def planner_reverse_pass():
#     global block
#     block_index = block_buffer_head
#
#     if ((block_buffer_head - block_buffer_tail) and (BLOCK_BUFFER_SIZE - 1)) > 3:
#         block_index = (block_buffer_head -3) and (BLOCK_BUFFER_SIZE - 1)
#         block[3] = []
#
#         while block_index not block_buffer_tail:
#             block_index = prev_block_index(block_index)
#             block[2] = block[1]
#             block[1] = block[0]
#             block[0] = block_buffer[block_index]
