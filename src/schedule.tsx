

enum TimeUnit {
    seconds,
    milliseconds,
    microseconds
}

class Schedule {
    name: string;
    description: string;
    time_unit: TimeUnit;

    tick_period: number;
    cycle_period: number;
    cycle_sub_period: number;

    constructor() {
        this.name = "";
        this.description = "";
        this.time_unit = TimeUnit.seconds;

        this.tick_period = 0;
        this.cycle_period = 0;
        this.cycle_sub_period = 0;
    }
}

class Task {
    name: string;
    description: string;
    length: number;
    frequency: number;
    start_tick: number;

    constructor() {
        this.name = "";
        this.description = "";
        this.length = 0;
        this.frequency = 0;
        this.start_tick = 0;
    }
}

