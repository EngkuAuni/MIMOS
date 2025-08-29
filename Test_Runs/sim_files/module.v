 Here is a simple Verilog module that fulfills the given specification:

```verilog
module counter (
    input clk,
    input rst,
    input up_down,
    input enable,
    input [3:0] count_in,
    output reg [3:0] count_out
);

reg [3:0] count = 4'b0001; // initialize counter to 1
assign count_in = count; // assign input for convenience

always @(posedge clk) begin
    if (enable) begin
        if (rst) begin
            count <= 4'b0000; // reset counter to 0 on reset
        end else if (up_down) begin
            if (count == 15'hF) begin // wrap around at F(15 decimal)
                count <= 4'b0000;
            end else begin
                count <= count + 1'b1; // increment counter
            end
        end else begin
            if (count == 4'b0000) begin // wrap around at 0
                count <= 15'hF;
            end else begin
                count <= count - 1'b1; // decrement counter
            end
        end
    end
end

assign count_out = count; // assign output for convenience

endmodule
```

This module implements a 4-bit synchronous up/down counter with reset and direction control. The counting is enabled by the `enable` input. When `up_down` is 1, the counter increments, and when it's 0, the counter decrements. The reset is asynchronous, but the counting logic only responds to changes on the rising edge of the clock signal (clk).