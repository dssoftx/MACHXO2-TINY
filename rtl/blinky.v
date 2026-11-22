// Blinky for the MachXO2-4000HC minimal board.
// 12 MHz XO on PCLKT0_1 (pin 128). LEDs active-high (FPGA -> 1k -> LED -> GND).
module top (
    input  wire       clk12,
    input  wire       btn0,      // active-low, enable internal pull-up (see .lpf)
    output wire [3:0] led
);
    reg [25:0] cnt = 0;
    always @(posedge clk12) cnt <= cnt + 1'b1;
    assign led = btn0 ? cnt[25:22] : 4'b1111;
endmodule

// No XO fitted? Use the internal oscillator instead:
//   wire clk; OSCH #(.NOM_FREQ("12.09")) osc (.STDBY(1'b0), .OSC(clk), .SEDSTDBY());
