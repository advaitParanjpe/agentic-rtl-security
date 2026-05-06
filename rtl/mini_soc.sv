`ifndef MINI_SOC_SV
`define MINI_SOC_SV

`include "soc_pkg.sv"

module mini_soc #(
  parameter bit BUG_SECRET_READ      = 1'b0,
  parameter bit BUG_STALE_RDATA      = 1'b0,
  parameter bit BUG_DEBUG_UNLOCK     = 1'b0,
  parameter bit BUG_USER_DEBUG_WRITE = 1'b0,
  parameter bit BUG_HIDDEN_ALIAS     = 1'b0,
  parameter bit BUG_RO_WRITE         = 1'b0
)(
  input  logic                  clk,
  input  logic                  rst_n,

  input  logic                  read_en,
  input  logic                  write_en,
  input  logic [soc_pkg::ADDR_W-1:0] addr,
  input  logic [soc_pkg::DATA_W-1:0] wdata,
  input  soc_pkg::priv_t        priv,

  output logic [soc_pkg::DATA_W-1:0] rdata,
  output logic                  resp_valid,
  output logic                  error
);

  import soc_pkg::*;

  // ------------------------------------------------------------
  // Internal registers
  // ------------------------------------------------------------

  logic [DATA_W-1:0] status_q;
  logic [DATA_W-1:0] config_q;
  logic [DATA_W-1:0] boot_lock_q;
  logic [DATA_W-1:0] debug_ctrl_q;
  logic [DATA_W-1:0] secret_key_q;
  logic [DATA_W-1:0] public_data_q;
  logic [DATA_W-1:0] hidden_dbg_q;
  logic [DATA_W-1:0] version_q;

  // Used only when BUG_STALE_RDATA is enabled.
  logic [DATA_W-1:0] last_rdata_q;

  // ------------------------------------------------------------
  // Basic address helpers
  // ------------------------------------------------------------

  logic addr_aligned;

  assign addr_aligned = (addr[1:0] == 2'b00);

  // ------------------------------------------------------------
  // Main sequential logic
  // ------------------------------------------------------------

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      status_q      <= RESET_STATUS;
      config_q      <= RESET_CONFIG;
      boot_lock_q   <= RESET_BOOT_LOCK;
      debug_ctrl_q  <= RESET_DEBUG_CTRL;
      secret_key_q  <= RESET_SECRET_KEY;
      public_data_q <= RESET_PUBLIC_DATA;
      hidden_dbg_q  <= RESET_HIDDEN_DBG;
      version_q     <= RESET_VERSION;

      rdata         <= ZERO_DATA;
      last_rdata_q  <= ZERO_DATA;
      resp_valid    <= 1'b0;
      error         <= 1'b0;
    end else begin
      // Defaults for cycles without an access.
      resp_valid <= 1'b0;
      error      <= 1'b0;
      rdata      <= ZERO_DATA;

      // Do not allow simultaneous read and write in this simple protocol.
      if (read_en && write_en) begin
        resp_valid <= 1'b1;
        error      <= 1'b1;
        rdata      <= BUG_STALE_RDATA ? last_rdata_q : ZERO_DATA;
      end

      // --------------------------------------------------------
      // Write path
      // --------------------------------------------------------

      else if (write_en) begin
        resp_valid <= 1'b1;

        if (!addr_aligned) begin
          error <= 1'b1;
        end else begin
          unique case (addr)

            ADDR_STATUS: begin
              // STATUS is read-only.
              if (BUG_RO_WRITE) begin
                status_q <= wdata;
                error    <= 1'b0;
              end else begin
                error <= 1'b1;
              end
            end

            ADDR_CONFIG: begin
              // CONFIG is public read/write.
              config_q <= wdata;
              error    <= 1'b0;
            end

            ADDR_BOOT_LOCK: begin
              // Only secure mode can write boot lock.
              if (priv == PRIV_SECURE) begin
                boot_lock_q <= wdata;
                error       <= 1'b0;
              end else begin
                error <= 1'b1;
              end
            end

            ADDR_DEBUG_CTRL: begin
              // USER must not write DEBUG_CTRL unless the bug is enabled.
              // Once boot_lock[0] is set, DEBUG_CTRL must not change unless
              // BUG_DEBUG_UNLOCK is enabled.
              if ((priv == PRIV_SECURE || BUG_USER_DEBUG_WRITE) &&
                  (!boot_lock_q[0] || BUG_DEBUG_UNLOCK)) begin
                debug_ctrl_q <= wdata;
                error        <= 1'b0;
              end else begin
                error <= 1'b1;
              end
            end

            ADDR_SECRET_KEY: begin
              // SECRET_KEY is secure-write only.
              if (priv == PRIV_SECURE) begin
                secret_key_q <= wdata;
                error        <= 1'b0;
              end else begin
                error <= 1'b1;
              end
            end

            ADDR_PUBLIC_DATA: begin
              // PUBLIC_DATA is public read/write.
              public_data_q <= wdata;
              error         <= 1'b0;
            end

            ADDR_HIDDEN_DBG: begin
              // Hidden debug state should never be directly writable.
              error <= 1'b1;
            end

            ADDR_VERSION: begin
              // VERSION is read-only.
              if (BUG_RO_WRITE) begin
                version_q <= wdata;
                error     <= 1'b0;
              end else begin
                error <= 1'b1;
              end
            end

            default: begin
              // Optional hidden alias bug.
              if (BUG_HIDDEN_ALIAS && addr == 8'h20) begin
                hidden_dbg_q <= wdata;
                error        <= 1'b0;
              end else begin
                error <= 1'b1;
              end
            end

          endcase
        end
      end

      // --------------------------------------------------------
      // Read path
      // --------------------------------------------------------

      else if (read_en) begin
        resp_valid <= 1'b1;

        if (!addr_aligned) begin
          error <= 1'b1;
          rdata <= BUG_STALE_RDATA ? last_rdata_q : ZERO_DATA;
        end else begin
          unique case (addr)

            ADDR_STATUS: begin
              rdata <= status_q;
              error <= 1'b0;
            end

            ADDR_CONFIG: begin
              rdata <= config_q;
              error <= 1'b0;
            end

            ADDR_BOOT_LOCK: begin
              rdata <= boot_lock_q;
              error <= 1'b0;
            end

            ADDR_DEBUG_CTRL: begin
              rdata <= debug_ctrl_q;
              error <= 1'b0;
            end

            ADDR_SECRET_KEY: begin
              // SECRET_KEY must not be readable by anyone in the clean design.
              if (BUG_SECRET_READ) begin
                rdata <= secret_key_q;
                error <= 1'b0;
              end else begin
                rdata <= BUG_STALE_RDATA ? last_rdata_q : ZERO_DATA;
                error <= 1'b1;
              end
            end

            ADDR_PUBLIC_DATA: begin
              rdata <= public_data_q;
              error <= 1'b0;
            end

            ADDR_HIDDEN_DBG: begin
              // Hidden debug state should never be readable.
              rdata <= BUG_STALE_RDATA ? last_rdata_q : ZERO_DATA;
              error <= 1'b1;
            end

            ADDR_VERSION: begin
              rdata <= version_q;
              error <= 1'b0;
            end

            default: begin
              // Optional hidden alias bug.
              if (BUG_HIDDEN_ALIAS && addr == 8'h20) begin
                rdata <= hidden_dbg_q;
                error <= 1'b0;
              end else begin
                rdata <= BUG_STALE_RDATA ? last_rdata_q : ZERO_DATA;
                error <= 1'b1;
              end
            end

          endcase
        end
      end

      // Track the previous read data value for stale-data bug experiments.
      if (resp_valid && !error) begin
        last_rdata_q <= rdata;
      end
    end
  end

endmodule

`endif