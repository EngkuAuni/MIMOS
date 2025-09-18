module uart_tx(
    input clk,
    input rst,
    input [7:0] data_in,
    input [2:0] baud_sel,
    input parity_en,
    output reg tx,
    output reg busy
);

parameter WIDTH = 8;
parameter STOP_BIT = 1;
parameter START_BIT = 0;

reg [2:0] baud_rate_divisor;
parameter BAUD_9600 = 100000000 / 960;0;
parameter BAUD_19200 = 100000000 / 1920;0;
parameter BAUD_38400 = 100000000 / 3840;0;
parameter BAUD_57600 = 100000000 / 5760;0;
parameter BAUD_115200 = 100000000 / 11520;0;

always @(*) begin
    case(baud_sel)
        3'b000: baud_rate_divisor <= BAUD_9600;
        3'b001: baud_rate_divisor <= BAUD_19200;
        3'b010: baud_rate_divisor <= BAUD_38400;
        3'b011: baud_rate_divisor <= BAUD_57600;
        3'b100: baud_rate_divisor <= BAUD_115200;
        default: baud_rate_divisor <= BAUD_9600;
    endcase
end

reg [15:0] baud_counter;
reg baud_tick;

always @(posedge clk) begin
    if(rst) begin
        baud_counter <= 0;
        baud_tick <= 0;
    end else begin
        if(baud_counter < baud_rate_divisor) begin
            baud_counter <= baud_counter + 1;
            baud_tick <= 0;
        end else begin
            baud_counter <= 0;
            baud_tick <= 1;
        end
    end
end

reg [3:0] state;
parameter IDLE = 0, START = 1, DATA = 2, PARITY = 3, STOP = 4;

reg [7:0] data_reg;
reg [3:0] data_bit;
reg parity_calc;

always @(posedge clk) begin
    if(rst) begin
        state <= IDLE;
        busy <= 0;
        tx <= 1;
        data_reg <= 0;
        data_bit <= 0;
        parity_calc <= 0;
    end else begin
        case(state)
            IDLE: begin
                if(data_in != 0 && !busy) begin
                    data_reg <= data_in;
                    state <= START;
                    busy <= 1;
                    tx <= START_BIT;
                end
            end
            START: begin
                if(baud_tick) begin
                    state <= DATA;
                    data_bit <= 0;
                end
            end
            DATA: begin
                if(baud_tick) begin
                    tx <= data_reg[data_bit];
                    data_bit <= data_bit + 1;
                    if(data_bit == WIDTH - 1) begin
                        if(parity_en)
                            state <= PARITY;
                        else
                            state <= STOP;
                    end
                end
            end
            PARITY: begin
                if(baud_tick) begin
                    parity_calc <= data_reg[0] ^ data_reg[1] ^ data_reg[2] ^ data_reg[3] ^ data_reg[4] ^ data_reg[5] ^ data_reg[6] ^ data_reg[7];
                    tx <= parity_calc;
                    state <= STOP;
                end
            end
            STOP: begin
                if(baud_tick) begin
                    tx <= STOP_BIT;
                    state <= IDLE;
                    busy <= 0;
                end
            end
        endcase
    end
end

endmodule