#include <cstdint>
#include "tdm_base.hpp"
#include "stubs/tdm_stub.hpp"

namespace tdm {

/***************************** CONSTRUCTOR/DESTRUCTOR *****************************/

BaseTdmScheduler::BaseTdmScheduler()
    : currentExecutingTask_(tdmTaskId_Idle),
    taskToExecute_(tdmTaskId_Idle),
    lastAllocatedTask_(tdmTaskId_Idle),
    currentTimeQuanta_(0),
    overrunTimeQuanta_(0)
{
}

BaseTdmScheduler::~BaseTdmScheduler()
{
}

/***************************** PUBLIC METHODS *****************************/


bool BaseTdmScheduler::scheduleCall()
{
    // Boolean to indicate whether the execution thread should be triggered
    // to execute a task
    bool triggerNewTask = false;

    // Get the task that is allocated for this time quanta
    tdmTaskId_e allocatedTask = getTaskAtTimeQuanta(currentTimeQuanta_);

    // Check if a task is running that shouldnt be at this time quanta,
    // excluding idle
    if ((allocatedTask != getCurrentExecutingTask()) &&
        (getCurrentExecutingTask() != tdmTaskId_Idle))  {
        // ERROR HERE!!!
        // Dont increment the time quanta, wait another tick until the running task is done
        overrunTimeQuanta_++;
        raiseTdmSchedulingError(currentTimeQuanta_, allocatedTask, getCurrentExecutingTask());
    }
    else {
        // No unexpected task execution, normal operation

        // Detect edge change, trigger task execution if edge is the start of a new
        // contiguous task allocation
        if ((lastAllocatedTask_ != allocatedTask) &&
            (allocatedTask != tdmTaskId_Idle))
        {

            setTaskToExecute(allocatedTask);
            triggerNewTask = true;
        }

        // Increment time quanta, wrap around max value
        currentTimeQuanta_++;
        if (currentTimeQuanta_ >= kCycleSize)
        {
            currentTimeQuanta_ = 0;
        }

        // Cache task allocation to detect edge change at next call
        lastAllocatedTask_ = allocatedTask;
    }
    return triggerNewTask;
}

tdmTaskId_e BaseTdmScheduler::getTaskAtTimeQuanta(uint32_t timeQuanta)
{
    tdmTaskId_e task;

    switch (kScheduleType)
    {
        case (tdmScheduleType_table): {
            task = getTaskAtTimeQuantaFromTable(timeQuanta);
            break;
        }
        case (tdmScheduleType_json): {
            task = getTaskAtTimeQuantaFromJson(timeQuanta);
            break;
        }
        case (tdmScheduleType_custom): {
            task = getTaskAtTimeQuantaFromCustom(timeQuanta);
            break;
        }
        default: {
            // Error
            task = tdmTaskId_Idle;
            break;
        }
    }
    return task;
}

tdmTaskId_e BaseTdmScheduler::getTaskAtTimeQuantaFromTable(uint32_t timeQuanta)
{
    return kScheduleTable[timeQuanta];
}

void BaseTdmScheduler::setCurrentExecutingTask(tdmTaskId_e taskId)
{
    currentExecutingTask_ = taskId;
}

void BaseTdmScheduler::setTaskToExecute(tdmTaskId_e taskId)
{
    taskToExecute_ = taskId;
}

tdmTaskId_e BaseTdmScheduler::getCurrentExecutingTask() const
{
    return currentExecutingTask_;
}

tdmTaskId_e BaseTdmScheduler::getTaskToExecute() const
{
    return taskToExecute_;
}

void BaseTdmScheduler::raiseTdmSchedulingError()
{
    // Default implementation - can be overridden by derived classes
    // or users can provide their own implementation
}

tdmTaskId_e BaseTdmScheduler::getTaskAtTimeQuantaFromCustom(uint32_t timeQuanta)
{
    // Default implementation returns idle - should be overridden in derived classes
    return tdmTaskId_Idle;
}

} // namespace tdm
