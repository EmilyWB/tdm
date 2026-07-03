typedef enum tdmTaskId_ {
    tdmTaskId_Idle,
    tdmTaskId_Task_100Hz,
    tdmTaskId_Task_10Hz,
    tdmTaskId_Task_1Hz,
} tdmTaskId_e;



typedef struct tdmTaskData_ {
    tdmTaskId_e id;
    tdm::Profiler profiler;
} tdmTaskData_t;
