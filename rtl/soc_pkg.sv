`ifndef SOC_PKG_SV
`define SOC_PKG_SV

package soc_pkg;

  // ------------------------------------------------------------
  // Basic bus widths
  // ------------------------------------------------------------

  parameter int ADDR_W = 8;
  parameter int DATA_W = 32;

  // ------------------------------------------------------------
  // Privilege levels
  // ------------------------------------------------------------

  typedef enum logic [0:0] {
    PRIV_USER   = 1'b0,
    PRIV_SECURE = 1'b1
  } priv_t;

  // ------------------------------------------------------------
  // Register addresses
  // ------------------------------------------------------------

  localparam logic [ADDR_W-1:0] ADDR_STATUS     = 8'h00;
  localparam logic [ADDR_W-1:0] ADDR_CONFIG     = 8'h04;
  localparam logic [ADDR_W-1:0] ADDR_BOOT_LOCK  = 8'h08;
  localparam logic [ADDR_W-1:0] ADDR_DEBUG_CTRL = 8'h0C;
  localparam logic [ADDR_W-1:0] ADDR_SECRET_KEY = 8'h10;
  localparam logic [ADDR_W-1:0] ADDR_PUBLIC_DATA = 8'h14;
  localparam logic [ADDR_W-1:0] ADDR_HIDDEN_DBG = 8'h18;
  localparam logic [ADDR_W-1:0] ADDR_VERSION    = 8'h1C;

  // ------------------------------------------------------------
  // Reset values
  // ------------------------------------------------------------

  localparam logic [DATA_W-1:0] RESET_STATUS      = 32'h0000_0000;
  localparam logic [DATA_W-1:0] RESET_CONFIG      = 32'h0000_0000;
  localparam logic [DATA_W-1:0] RESET_BOOT_LOCK   = 32'h0000_0000;
  localparam logic [DATA_W-1:0] RESET_DEBUG_CTRL  = 32'h0000_0000;
  localparam logic [DATA_W-1:0] RESET_SECRET_KEY  = 32'h0000_0000;
  localparam logic [DATA_W-1:0] RESET_PUBLIC_DATA = 32'h0000_0000;
  localparam logic [DATA_W-1:0] RESET_HIDDEN_DBG  = 32'hCAFE_BABE;
  localparam logic [DATA_W-1:0] RESET_VERSION     = 32'h0000_0001;

  // ------------------------------------------------------------
  // Useful constants
  // ------------------------------------------------------------

  localparam logic [DATA_W-1:0] ZERO_DATA = 32'h0000_0000;

endpackage

`endif