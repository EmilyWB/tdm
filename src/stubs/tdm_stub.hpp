typedef enum tdmTaskId_ {
    tdmTaskId_Idle,
!<TASK_ID_TYPEDEF>!
} tdmTaskId_e;



typedef struct tdmTaskData_ {
    tdmTaskId_e id;
    !<PROFILER_NAMESPACE>!::Profiler profiler;
} tdmTaskData_t;
