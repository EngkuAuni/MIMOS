# IC Design specifications

## User Flow
[1] User enters spec → HDL is generated
     ↳ Fails validation? Show warning + let user fix in text area
     ↳ Passes validation? Proceed

[2] User reviews HDL → manually edits if needed → clicks "Generate Testbench"

[3] If testbench fails → show fallback or error explanation

[4] Run simulation


Example UART HDL Code + testbench for simulation testing
UART is commonly used in satellite subsystems for:
	•	Telemetry data transmission
	•	Command/response interfaces
	•	Redundant backup links


## HDL Code Example

module uart_tx (
    input clk,
    input rst,
    input tx_start,
    input [7:0] data_in,
    output reg tx,
    output reg busy
);
    parameter IDLE = 2'b00;
    parameter START = 2'b01;
    parameter DATA = 2'b10;
    parameter STOP = 2'b11;

    reg [1:0] state = IDLE;
    reg [2:0] bit_cnt = 0;
    reg [7:0] tx_buffer = 0;

    always @(posedge clk or posedge rst) begin
        if (rst) begin
            state <= IDLE;
            tx <= 1'b1;
            busy <= 1'b0;
            bit_cnt <= 0;
            tx_buffer <= 0;
        end else begin
            case (state)
                IDLE: begin
                    tx <= 1'b1;
                    busy <= 1'b0;
                    if (tx_start) begin
                        tx_buffer <= data_in;
                        state <= START;
                        busy <= 1'b1;
                    end
                end
                START: begin
                    tx <= 1'b0;  // Start bit
                    state <= DATA;
                    bit_cnt <= 0;
                end
                DATA: begin
                    tx <= tx_buffer[bit_cnt];
                    bit_cnt <= bit_cnt + 1;
                    if (bit_cnt == 3'd7)
                        state <= STOP;
                end
                STOP: begin
                    tx <= 1'b1;  // Stop bit
                    state <= IDLE;
                end
            endcase
        end
    end
endmodule

## Testbench Code Example

module tb_uart_tx;
    reg clk = 0;
    reg rst = 1;
    reg tx_start = 0;
    reg [7:0] data_in = 8'hA5;
    wire tx;
    wire busy;

    uart_tx uut (
        .clk(clk),
        .rst(rst),
        .tx_start(tx_start),
        .data_in(data_in),
        .tx(tx),
        .busy(busy)
    );

    // 10ns clock
    always #5 clk = ~clk;

    initial begin
        $dumpfile("wave.vcd");
        $dumpvars(0, uut);

        $monitor("Time=%0t | tx=%b | busy=%b", $time, tx, busy);

        #10 rst = 0;
        #20 tx_start = 1;
        #10 tx_start = 0;
        #200 $finish;
    end
endmodule