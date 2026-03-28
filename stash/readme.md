

## Nomenclature

- Tick/Quanta/Slice: These are interchangeable descriptions of the fundamental units of time that the schedule executes at, typically the RTOS tick rate derived from a dedicated hardware clock
- Cycle: The total??
- Cycle Size: Number of ticks/quanta/slices in a whole cycle


## Schedule Description

What are the parameters of the schedule:

- Tick period: The length of each time quanta in seconds
- Cycle period: The total length of the periodic cycle
- Tasks
    - Task Name:
    - Task assigned length:
    - Task Execution Frequency

So, here is an example of parameters that make up a schedule, with no particular format:

- 1ms tick period
- 1s cycle period
- Task 1
    - Jeff
    - 8ms time allocation
    - 50Hz execution Frequency
- Task 2
    - Amanda
    - 1ms time allocation
    - 200Hz execution Frequency


## Schedule Files

### Schedule JSON Definition Schema

The schedule JSON schema file defines the contents of the schedule JSON file. I shall describe the contents of this file in plain text, which is based on the schedule description above

- Name [str] : Name of the schedule
- Description [str] : Arbitrary string field description
- Time Unit[enum] : Time unit: microsecond, millisecond, seconds. The period and time measurements will be in these time units.
- Tick Period [float] : Fundamental time period of the schedule, in seconds
- Cycle Period [float] : Total cycle time of the schedule, in seconds
- Sub-cycle Period [float] : Optional variable, sometimes useful for representing the schedule as a 2D matrix with a sub-period within the main cycle in seconds. For example, it may be useful to visualise a 1s cycle time with 100ms sub-periods if looking at it visually. Otherwise the output will display as one long array.
- Tasks [list] : [
    - Task [object] : {
        - Task Name [str] : Name of task
        - Task Assigned Time [float] : Time assigned for this task. This MUST be multiples of the tick period
        - Task Execution Frequency [float] : 
        - Task Execution Start Time [number] : This is optional, the user may put this in if they want to. Otherwise the tool can calculate it
    }
]

### Schedule JSON Definition

The schedule

### Schedule Table

## Tools

### Plain Text Editing

The 

### Webpage editor

User input:

- Schedule definition JSON
- Schedule definition JSON schema (pre uploaded)

Output:

- Modified schedule definition JSON
- Generated C code

Why webpage; well, i thought that maybe having a python script/exe would be better, but that is not very portable. It would be easier to just have a webpage that runs locally.

So what would this be. On full screen, it would be a single page; it had a left hand pane, which shows an editor for the schedule JSON file. The right hand pane is the schedule table graphical view. If its a slim or small screen, then instead of the screen in two halves it will have a button to swap between the editor and graphical view.

So the editor view wont be a plain text editor, it will have some basic UI that represents it. 

### Python Code Generator Script

User input:

- Schedule definition JSON
- Schedule definition JSON schema

Output:

- Generated C code




#### Stub Replacers

##### TASK_ID_TYPEDEF

- Enumerations of task IDS in the format `tdmTaskId_TASKNAME`
- Each task name has its own enumeration. 
- Generated from the JSON task definitions

##### TDM_NAMESPACE

- Namespace of TDM code
- Defaults to `tdm`
- User string input

##### PROFILER_NAMESPACE

- Namespace of profiler code
- Defaults to `tdm`
- User string input

##### QUANTA_UNIT

- Unsigned integer that tracks
- Defaults to `unsigned int`, and may be one of the following:
    - uint8_t, uint16_t, uint8_least_t, etc
- User must choose an appropriately sized value to prevent overflow
- User string input 

##### SCHEDULE_TYPE

- May be one of three possible values:
    - `table`
    - `json`
    - `custom`
- This is translated to the enumeration in code `scheduleType_e`
- User string input

##### CYCLE_SIZE

- Size of the TDM cycle
- User integer input

##### EXECUTION_CALLS


``` C++
case (tdmTaskId_X): {
    setCurrentExecutingTask(tdmTaskId_X);

    setCurrentExecutingTask(tdmTaskId_Idle);
    break;
}


```
