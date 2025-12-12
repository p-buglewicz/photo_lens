const { createApp } = Vue;

createApp({
  data() {
    return {
      apiBase: this.resolveApiBase?.() || "",
      loading: false,
      error: null,
      info: "",
      batchId: null,
      statusText: "Idle",
      processed: 0,
      total: null,
      poller: null,
      recentFiles: [], // Array of {name, timestamp} for animation
      websocket: null,
      ingestConfig: {
        limit: null,
        reprocess: false,
      },
    };
  },
  computed: {
    isDone() {
      return this.statusText === "completed";
    },
  },
  methods: {
    resolveApiBase() {
      const explicit = window.API_BASE || window.__API_BASE__;
      if (explicit) return explicit.replace(/\/$/, "");

      const { hostname, port, protocol } = window.location;

      // In docker-compose we often hit frontend at 8080; backend is published on 8001
      if (
        (hostname === "localhost" || hostname === "127.0.0.1") &&
        (port === "8080" || port === "80")
      ) {
        return `${protocol}//${hostname}:8001`;
      }

      // Fallback: same origin
      return window.location.origin;
    },
    connectWebSocket() {
      const wsProtocol = this.apiBase.startsWith("https") ? "wss" : "ws";
      const wsBase = this.apiBase.replace(/^https?:\/\//, "");
      const wsUrl = `${wsProtocol}://${wsBase}/ws/ingest/progress`;

      this.websocket = new WebSocket(wsUrl);

      this.websocket.onopen = () => {
        console.log("✅ WebSocket connected");
      };

      this.websocket.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.type === "file_processed") {
          this.recentFiles.unshift({
            name: data.filename,
            timestamp: Date.now(),
          });
          if (this.recentFiles.length > 10) {
            this.recentFiles = this.recentFiles.slice(0, 10);
          }
        }
      };

      this.websocket.onerror = (error) => {
        console.error("❌ WebSocket error:", error);
      };

      this.websocket.onclose = () => {
        // Always reconnect after 2 seconds
        setTimeout(() => this.connectWebSocket(), 2000);
      };
    },
    disconnectWebSocket() {
      if (this.websocket) {
        this.websocket.close();
        this.websocket = null;
      }
    },
    async startIngestion() {
      this.loading = true;
      this.error = null;
      this.info = "Triggering ingestion...";

      try {
        const params = new URLSearchParams();
        if (this.ingestConfig.limit !== null && this.ingestConfig.limit !== "") {
          params.append("limit", this.ingestConfig.limit);
        }
        if (this.ingestConfig.reprocess !== null) {
          params.append("reprocess", this.ingestConfig.reprocess ? "true" : "false");
        }

        const qs = params.toString();
        const url = qs ? `${this.apiBase}/ingest/start?${qs}` : `${this.apiBase}/ingest/start`;
        const response = await fetch(url, { method: "POST" });
        if (!response.ok) {
          const detail = await response.text();
          throw new Error(detail || "Failed to start ingestion");
        }

        const data = await response.json();
        this.batchId = data.batch_id;
        this.statusText = data.status || "started";
        this.info = "Ingestion started.";
        this.recentFiles = []; // Clear previous run
        this.startPolling();
        await this.refreshStatus();
      } catch (err) {
        this.error = err?.message || "Unable to start ingestion.";
        this.info = "";
      } finally {
        this.loading = false;
      }
    },
    startPolling() {
      if (this.poller) {
        clearInterval(this.poller);
      }
      this.poller = setInterval(this.refreshStatus, 2000);
    },
    stopPolling() {
      if (this.poller) {
        clearInterval(this.poller);
        this.poller = null;
      }
    },
    async refreshStatus() {
      try {
        const response = await fetch(`${this.apiBase}/ingest/status?limit=1`);
        if (!response.ok) {
          throw new Error("Unable to fetch status");
        }

        const payload = await response.json();
        const latest = payload.items?.[0];

        if (!latest) {
          this.statusText = "waiting";
          this.info = "No ingestion batches found yet.";
          return;
        }

        this.batchId = this.batchId || latest.batch_id;
        this.statusText = latest.status || "unknown";
        this.processed = latest.processed_files || 0;
        this.total = latest.total_files ?? null;
        this.info = latest.completed_at ? "Ingestion finished." : "Ingestion running...";

        if (this.statusText === "failed") {
          this.error = latest.error_message || "Ingestion failed.";
          this.stopPolling();
        }

        if (this.statusText === "completed") {
          this.stopPolling();
        }
      } catch (err) {
        this.error = err?.message || "Unable to read status.";
        this.stopPolling();
      }
    },
  },
  mounted() {
    this.connectWebSocket();
    this.refreshStatus();
    this.startPolling();
  },
  unmounted() {
    this.stopPolling();
    this.disconnectWebSocket();
  },
}).mount("#app");
