module tb_uart_tx;
    reg clk;
    reg rst;
    reg [7:0] data_in;
    reg [2:0] baud_sel;
    reg parity_en;
    wire tx;
    wire busy;

    uart_tx UUT(
        .clk(clk),
        .rst(rst),
        .data_in(data_in),
        .baud_sel(baud_sel),
        .parity_en(parity_en),
        .tx(tx),
        .busy(busy)
    );

    always #5 clk = ~clk;

    initial begin
        clk = 0;
        rst = 1;
        data_in = 0;
        baud_sel = 0;
        parity_en = 0;
        #10 rst = 0;
        #20 data_in = 8'h55;
        $dumpfile("sim_files/wave.vcd");
        $dumpvars(0, UUT);
        $finish;
    end
endmodule