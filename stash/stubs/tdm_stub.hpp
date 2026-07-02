
!<AUTO_GENERATION_HEADER>!

#ifndef TDM_HPP
#define TDM_HPP

#include <cstdint>

namespace !<TDM_NAMESPACE>! {

/***************************** TYPEDEFS *****************************/

typedef enum tdmTaskId_ {
    tdmTaskId_Idle,
!<TASK_ID_TYPEDEF>!
} tdmTaskId_e;

typedef struct tdmTaskData_ {
    tdmTaskId_e id;
    !<PROFILER_NAMESPACE>!::Profiler profiler;
} tdmTaskData_t;

typedef enum scheduleType_ {
    tdmScheduleType_table,
    tdmScheduleType_json,
    tdmScheduleType_custom
} scheduleType_e;



/***************************** TDM SCHEDULER CLASS *****************************/

class BaseTdmScheduler {
public:
    // Constructor
    BaseTdmScheduler();
    
    // Destructor
    virtual ~BaseTdmScheduler();

    // Public methods
    bool scheduleCall();
    void executeCall();

protected:
    // Getters and setters - default implementations provided, override for thread-safety
    virtual void setCurrentExecutingTask(tdmTaskId_e taskId);
    virtual void setTaskToExecute(tdmTaskId_e taskId);
    virtual tdmTaskId_e getCurrentExecutingTask() const;
    virtual tdmTaskId_e getTaskToExecute() const;

    // User-overridable hooks
    virtual tdmTaskId_e getTaskAtTimeQuantaFromCustom(!<QUANTA_UNIT>! timeQuanta);
    virtual void raiseTdmSchedulingError();

private:
    tdmTaskId_e getTaskAtTimeQuanta(!<QUANTA_UNIT>! timeQuanta);
    tdmTaskId_e getTaskAtTimeQuantaFromTable(!<QUANTA_UNIT>! timeQuanta);
    tdmTaskId_e getTaskAtTimeQuantaFromJson(!<QUANTA_UNIT>! timeQuanta);

    tdmTaskId_e currentExecutingTask_;
    tdmTaskId_e taskToExecute_;
    tdmTaskId_e lastAllocatedTask_;
    !<QUANTA_UNIT>! currentTimeQuanta_;
    !<QUANTA_UNIT>! overrunTimeQuanta_;

    // Static constants
    static const scheduleType_e kScheduleType;
    static const !<QUANTA_UNIT>! kCycleSize;
    static const !<QUANTA_UNIT>! kNumberOfTasks;
    static const tdmTaskId_e kScheduleTable[kCycleSize];
    static const tdmTaskData_t kTaskData[kNumberOfTasks];
};

} // namespace !<TDM_NAMESPACE>!

#endif // TDM_HPP
