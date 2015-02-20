from sam3x_helper import uint32_t, uint64_t, uint, int32_t, int16_t
import plannercpp
from config import HAL_TIMER_RATE, MAX_STEP_FREQUENCY, DOUBLE_FREQUENCY, F_CPU
import matplotlib.pyplot as plt
from util import speed_lookuptable_fast, speed_lookuptable_slow


current_block = plannercpp.calculate_trapezoid_for_block(plannercpp.current_block, 0, 0)  # calculate current_block


# reset some counter
step_events_completed = 0
HAL_timer_complete = 0
acc_step_rate = 0

MULTI24 = 0


def MultiU24X24toH16(longIn1, longIn2):
    return uint32_t(uint(((uint64_t(longIn1) >> MULTI24) * longIn2), 64) >> (24-MULTI24))

def MultiU16X8toH16(longIn1, longIn2):
    return uint32_t(uint((longIn1 * longIn2), 32) >> 16)

# This is a simulation, so I don't need quadstepping for now

first_in_quad = True
first_in_double = True


def calc_timer(step_rate):
    global step_loops
    global first_in_quad, first_in_double

    step_rate = step_rate if step_rate < MAX_STEP_FREQUENCY else MAX_STEP_FREQUENCY
    step_rate = uint(step_rate, 16)

    if step_rate > (2 * DOUBLE_FREQUENCY):
        if first_in_quad:
            print("quadstepping at {} steps".format(step_rate))
            first_in_quad = False
            first_in_double = True
        step_rate >>= 2
        step_loops = 4
    elif step_rate > DOUBLE_FREQUENCY:
        if first_in_double:
            print("doublestepping at {} steps".format(step_rate))
            first_in_quad = True
            first_in_double = False
        step_rate >>= 1
        step_loops = 2
    else:
        step_loops = 1
        
    if step_rate < F_CPU / 500000:
        step_rate = F_CPU / 500000
    step_rate -= (F_CPU / 500000)
    if step_rate >= (8*256):
        # print('fast')
        step_element = int(step_rate) >> 8
        table_address = step_element >> 1

        tmp_step_rate = int(step_rate) & 0x00ff

        gain = speed_lookuptable_fast[table_address][0]

        timer = MultiU16X8toH16(tmp_step_rate, gain)
        timer = speed_lookuptable_fast[table_address][0] - timer

    else:
        # print('slow: {}'.format(step_rate))
        step_element = 0
        step_element += (int(step_rate) >> 1) & 0xfffc

        table_address = step_element >> 2
        timer = speed_lookuptable_slow[table_address - 1][0]

        timer -= (speed_lookuptable_slow[table_address][1] * (uint(step_rate, 8) & 0x0007)) >> 3


    # step_rate = step_rate if step_rate > 210 else 210
    # timer = HAL_TIMER_RATE / step_rate
    # timer = uint32_t(timer)
    return int(timer)


def calc_new_timer(step_rate):
    global step_loops
    global first_in_quad, first_in_double

    step_rate = step_rate if step_rate < MAX_STEP_FREQUENCY else MAX_STEP_FREQUENCY
    step_rate = uint(step_rate, 16)

    if step_rate > (2 * DOUBLE_FREQUENCY):
        if first_in_quad:
            print("quadstepping at {} steps".format(step_rate))
            first_in_quad = False
            first_in_double = True
        step_rate >>= 2
        step_loops = 4
    elif step_rate > DOUBLE_FREQUENCY:
        if first_in_double:
            print("doublestepping at {} steps".format(step_rate))
            first_in_quad = True
            first_in_double = False
        step_rate >>= 1
        step_loops = 2
    else:
        step_loops = 1

    step_rate = step_rate if step_rate > 210 else 210
    timer = HAL_TIMER_RATE / step_rate
    timer = uint32_t(timer)
    return int(timer)


def trapezoid_generator_reset():
    global deceleration_time
    global OCR1A_nominal, step_loops_nominal, acceleration_time, HAL_timer_set_count, acc_step_rate
    global actual_step_rate

    deceleration_time = 0
    OCR1A_nominal = calc_timer(current_block.nominal_rate)
    OCR1A_nominal = uint32_t(OCR1A_nominal)

    step_loops_nominal = step_loops
    acc_step_rate = current_block.initial_rate
    acc_step_rate = uint32_t(acc_step_rate)

    acceleration_time = calc_timer(acc_step_rate)
    acceleration_time = uint32_t(acceleration_time)

    HAL_timer_set_count = acceleration_time
    actual_step_rate = acc_step_rate

first_acc_until = True
first_dec_after = True
dec_after = 0
first_else = True
last_step_rate = 0


def ISR_workhorse(my_timer):
    global step_events_completed, HAL_timer_set_count, step_loops, deceleration_time, acceleration_time, acc_step_rate
    global first_acc_until, first_dec_after, first_else
    global dec_after
    global HAL_timer_complete
    global actual_step_rate
    global last_step_rate
    # check current_block != 0
    # stepper control

    # calculation of the new timer
    # this is what we want to see
    # first you need to set the step_events_completed to 0!
    #
    # calculate current_block (done with import/run this file)
    #
    # now you can run the workhorse with run_it(steps)
    # steps is ~ TRAVEL_IN_MM * STEP_PER_MM (take a look in config.py)

    if step_events_completed <= current_block.accelerate_until:
        acc_step_rate = MultiU24X24toH16(acceleration_time, current_block.acceleration_rate)

        if acc_step_rate > current_block.nominal_rate:
            acc_step_rate = current_block.nominal_rate

        # timer = calc_timer(acc_step_rate)
        timer = my_timer(acc_step_rate)
        HAL_timer_set_count = timer
        actual_step_rate = acc_step_rate

        acceleration_time += timer
        acceleration_time = int32_t(acceleration_time)

        if first_acc_until:
            print("first_acc_until: {0} with speed: {1} last_step_rate {2}".format(step_events_completed,
                                                                                   acc_step_rate,
                                                                                   last_step_rate))
            first_acc_until = False
            first_dec_after = True
        last_step_rate = acc_step_rate

    elif step_events_completed > current_block.decelerate_after:

        step_rate = MultiU24X24toH16(deceleration_time, current_block.acceleration_rate)

        if step_rate > acc_step_rate:
            step_rate = current_block.final_rate
            #print('xTruex')
        else:
            step_rate = acc_step_rate - step_rate
            #print(step_rate)

        # timer = calc_timer(step_rate)
        timer = my_timer(step_rate)
        HAL_timer_set_count = timer
        actual_step_rate = step_rate

        deceleration_time += timer
        deceleration_time = int32_t(deceleration_time)

        if first_dec_after:
            print("first_dec_after: {0} with speed: {1} last_step_rate {2}".format(step_events_completed,
                                                                                   step_rate,
                                                                                   last_step_rate))
            first_dec_after = False
            first_acc_until = True
            dec_after = HAL_timer_complete

        last_step_rate = step_rate

    else:
        if first_else:
            print('first_plateau: {0} with speed: {1}'.format(step_events_completed, acc_step_rate))
            first_else = False
        HAL_timer_set_count = OCR1A_nominal
        actual_step_rate = current_block.nominal_rate

        step_loops = step_loops_nominal

    HAL_timer_complete += HAL_timer_set_count


list_of_acc_step_rate = []
list_of_timer_complete = []


def run_it(steps):
    global step_events_completed
    global list_of_acc_step_rate
    global list_of_timer_complete
    last_acc = 0

    list_of_acc_step_rate.clear()
    list_of_timer_complete.clear()
    trapezoid_generator_reset()
    list_of_acc_step_rate.append(actual_step_rate)
    list_of_timer_complete.append(HAL_timer_complete)
    # for step_events_completed in range(0, steps-1):
    while step_events_completed < (steps-1):
        ISR_workhorse(calc_timer)
        list_of_acc_step_rate.append(actual_step_rate)
        list_of_timer_complete.append(HAL_timer_complete)
        step_events_completed += 1*step_loops
        # print(step_events_completed)
        if last_acc == actual_step_rate and actual_step_rate < 150:
            print("break at: {}".format(step_events_completed))
            break
        last_acc = actual_step_rate
    print('last: {0}\nspeed: {1}'.format(HAL_timer_complete, actual_step_rate))


def show_plot():
    plt.close('all')

    f, axarr = plt.subplots(2, sharey=True)

    axarr[0].step(list_of_timer_complete, list_of_acc_step_rate, 'k', label='HAL_timer')
    steps = range(0, len(list_of_acc_step_rate))
    print(len(list_of_acc_step_rate))
    axarr[1].step(steps, list_of_acc_step_rate)
    plt.ylim(0, current_block.nominal_rate*1.05)

    plt.show()


def auto_mode(steps):
    run_it(steps)
    show_plot()
