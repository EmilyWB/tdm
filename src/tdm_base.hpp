

#ifndef TDM_HPP
#define TDM_HPP

#include <cstdint>

namespace tdm {

/***************************** TYPEDEFS *****************************/

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
    virtual tdmTaskId_e getTaskAtTimeQuantaFromCustom(uint32_t timeQuanta);
    virtual void raiseTdmSchedulingError();

private:
    tdmTaskId_e getTaskAtTimeQuanta(uint32_t timeQuanta);
    tdmTaskId_e getTaskAtTimeQuantaFromTable(uint32_t timeQuanta);
    tdmTaskId_e getTaskAtTimeQuantaFromJson(uint32_t timeQuanta);

    tdmTaskId_e currentExecutingTask_;
    tdmTaskId_e taskToExecute_;
    tdmTaskId_e lastAllocatedTask_;
    uint32_t currentTimeQuanta_;
    uint32_t overrunTimeQuanta_;

    // Static constants
    static const scheduleType_e kScheduleType;
    static const uint32_t kCycleSize;
    static const uint32_t kNumberOfTasks;
    static const tdmTaskId_e kScheduleTable[kCycleSize];
    static const tdmTaskData_t kTaskData[kNumberOfTasks];
};

} // namespace tdm

#endif // TDM_HPP
