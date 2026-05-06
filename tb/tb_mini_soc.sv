`timescale 1ns/1ps

`include "../rtl/soc_pkg.sv"
`include "../rtl/mini_soc.sv"

module tb_mini_soc;

  import soc_pkg::*;

  // ------------------------------------------------------------
  // Clock/reset
  // ------------------------------------------------------------

  logic clk;
  logic rst_n;

  initial begin
    clk = 1'b0;
    forever #5 clk = ~clk;   // 100 MHz clock
  end

  // ------------------------------------------------------------
  // DUT inputs
  // ------------------------------------------------------------

  logic read_en;
  logic write_en;
  logic [ADDR_W-1:0] addr;
  logic [DATA_W-1:0] wdata;
  priv_t priv;

  // ------------------------------------------------------------
  // DUT outputs
  // ------------------------------------------------------------

  logic [DATA_W-1:0] rdata;
  logic resp_valid;
  logic error;

  // ------------------------------------------------------------
  // DUT instance
  // ------------------------------------------------------------

`ifndef BUG_SECRET_READ
`define BUG_SECRET_READ 0
`endif

`ifndef BUG_STALE_RDATA
`define BUG_STALE_RDATA 0
`endif

`ifndef BUG_DEBUG_UNLOCK
`define BUG_DEBUG_UNLOCK 0
`endif

`ifndef BUG_USER_DEBUG_WRITE
`define BUG_USER_DEBUG_WRITE 0
`endif

`ifndef BUG_HIDDEN_ALIAS
`define BUG_HIDDEN_ALIAS 0
`endif

`ifndef BUG_RO_WRITE
`define BUG_RO_WRITE 0
`endif

mini_soc #(
.BUG_SECRET_READ      (`BUG_SECRET_READ),
.BUG_STALE_RDATA      (`BUG_STALE_RDATA),
.BUG_DEBUG_UNLOCK     (`BUG_DEBUG_UNLOCK),
.BUG_USER_DEBUG_WRITE (`BUG_USER_DEBUG_WRITE),
.BUG_HIDDEN_ALIAS     (`BUG_HIDDEN_ALIAS),
.BUG_RO_WRITE         (`BUG_RO_WRITE)
    ) dut (
    .clk        (clk),
    .rst_n      (rst_n),
    .read_en    (read_en),
    .write_en   (write_en),
    .addr       (addr),
    .wdata      (wdata),
    .priv       (priv),
    .rdata      (rdata),
    .resp_valid (resp_valid),
    .error      (error)
  );

  // ------------------------------------------------------------
  // Testbench bookkeeping
  // ------------------------------------------------------------

  int num_tests;
  int num_fails;

  // ------------------------------------------------------------
  // Basic reset task
  // ------------------------------------------------------------

  task automatic apply_reset();
    begin
      rst_n    = 1'b0;
      read_en  = 1'b0;
      write_en = 1'b0;
      addr     = '0;
      wdata    = '0;
      priv     = PRIV_USER;

      repeat (3) @(posedge clk);
      rst_n = 1'b1;
      repeat (2) @(posedge clk);
    end
  endtask

  // ------------------------------------------------------------
  // MMIO write task
  // ------------------------------------------------------------

  task automatic mmio_write(
    input logic [ADDR_W-1:0] write_addr,
    input logic [DATA_W-1:0] write_data,
    input priv_t             write_priv,
    input bit                expected_error
  );
    begin
      @(negedge clk);
      addr     = write_addr;
      wdata    = write_data;
      priv     = write_priv;
      write_en = 1'b1;
      read_en  = 1'b0;

      @(posedge clk);
      #1;

      num_tests++;

      if (resp_valid !== 1'b1) begin
        $display("[FAIL] WRITE addr=0x%02h expected resp_valid=1, got %0b",
                 write_addr, resp_valid);
        num_fails++;
      end

      if (error !== expected_error) begin
        $display("[FAIL] WRITE addr=0x%02h expected error=%0b, got %0b",
                 write_addr, expected_error, error);
        num_fails++;
      end else begin
        $display("[PASS] WRITE addr=0x%02h data=0x%08h priv=%s error=%0b",
                 write_addr,
                 write_data,
                 write_priv == PRIV_SECURE ? "SECURE" : "USER",
                 error);
      end

      @(negedge clk);
      write_en = 1'b0;
      addr     = '0;
      wdata    = '0;
      priv     = PRIV_USER;
    end
  endtask

  // ------------------------------------------------------------
  // MMIO read task
  // ------------------------------------------------------------

  task automatic mmio_read(
    input  logic [ADDR_W-1:0] read_addr,
    input  priv_t             read_priv,
    input  logic [DATA_W-1:0] expected_rdata,
    input  bit                expected_error
  );
    begin
      @(negedge clk);
      addr     = read_addr;
      wdata    = '0;
      priv     = read_priv;
      write_en = 1'b0;
      read_en  = 1'b1;

      @(posedge clk);
      #1;

      num_tests++;

      if (resp_valid !== 1'b1) begin
        $display("[FAIL] READ addr=0x%02h expected resp_valid=1, got %0b",
                 read_addr, resp_valid);
        num_fails++;
      end

      if (error !== expected_error || rdata !== expected_rdata) begin
        $display("[FAIL] READ addr=0x%02h priv=%s expected rdata=0x%08h error=%0b, got rdata=0x%08h error=%0b",
                 read_addr,
                 read_priv == PRIV_SECURE ? "SECURE" : "USER",
                 expected_rdata,
                 expected_error,
                 rdata,
                 error);
        num_fails++;
      end else begin
        $display("[PASS] READ addr=0x%02h priv=%s rdata=0x%08h error=%0b",
                 read_addr,
                 read_priv == PRIV_SECURE ? "SECURE" : "USER",
                 rdata,
                 error);
      end

      @(negedge clk);
      read_en = 1'b0;
      addr    = '0;
      priv    = PRIV_USER;
    end
  endtask

  // ------------------------------------------------------------
  // Main test
  // ------------------------------------------------------------

  initial begin
    num_tests = 0;
    num_fails = 0;

    $display("========================================");
    $display("Starting mini_soc security testbench");
    $display("========================================");

    apply_reset();

    // ----------------------------------------------------------
// Test 1: normal public register write/read
// ----------------------------------------------------------

$display("\n[TEST] Public register access should work");

mmio_write(ADDR_PUBLIC_DATA, 32'h1234_ABCD, PRIV_USER, 1'b0);

mmio_read(ADDR_PUBLIC_DATA, PRIV_USER, 32'h1234_ABCD, 1'b0);

// ----------------------------------------------------------
// Test 2: secure write to SECRET_KEY should work
// ----------------------------------------------------------

$display("\n[TEST] Secure write to SECRET_KEY should work");

mmio_write(ADDR_SECRET_KEY, 32'hDEAD_BEEF, PRIV_SECURE, 1'b0);

// ----------------------------------------------------------
// Test 3: user read from SECRET_KEY should be blocked
// ----------------------------------------------------------

$display("\n[TEST] User read from SECRET_KEY should be blocked");

mmio_read(ADDR_SECRET_KEY, PRIV_USER, 32'h0000_0000, 1'b1);

// ----------------------------------------------------------
// Test 4: secure read from SECRET_KEY should also be blocked
// ----------------------------------------------------------

$display("\n[TEST] Secure read from SECRET_KEY should also be blocked");

mmio_read(ADDR_SECRET_KEY, PRIV_SECURE, 32'h0000_0000, 1'b1);

    // ----------------------------------------------------------
    // Final result
    // ----------------------------------------------------------

    $display("\n========================================");
    $display("Test summary: %0d checks, %0d failures", num_tests, num_fails);
    $display("========================================");

    if (num_fails == 0) begin
      $display("RESULT: PASS");
    end else begin
      $display("RESULT: FAIL");
    end

    $finish;
  end

endmodule