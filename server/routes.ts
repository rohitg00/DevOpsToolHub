import { Express } from 'express';
import { supabase } from './db';

export function routes(app: Express) {
  // Middleware to log all requests
  app.use((req, res, next) => {
    console.log(`[${new Date().toISOString()}] ${req.method} ${req.url}`);
    next();
  });

  // Get all tools
  app.get("/api/tools", async (req, res) => {
    try {
      console.log("Fetching all tools...");
      const { data: tools, error } = await supabase
        .from("tools")
        .select("*");

      if (error) {
        console.error("Supabase error:", error);
        throw error;
      }
      
      console.log(`Found ${tools?.length || 0} tools`);
      res.json(tools || []);
    } catch (error) {
      console.error("Error fetching tools:", error);
      res.status(500).json({ message: "Error fetching tools" });
    }
  });

  // Get a specific tool
  app.get("/api/tools/:name", async (req, res) => {
    try {
      const toolName = req.params.name;
      console.log(`Fetching tool: ${toolName}`);
      
      const { data: tool, error } = await supabase
        .from("tools")
        .select("*")
        .eq("name", toolName)
        .single();

      if (error) {
        console.error("Supabase error:", error);
        throw error;
      }

      if (!tool) {
        console.log(`Tool not found: ${toolName}`);
        return res.status(404).json({ message: "Tool not found" });
      }

      console.log(`Found tool: ${toolName}`);
      res.json(tool);
    } catch (error) {
      console.error("Error fetching tool:", error);
      res.status(500).json({ message: "Error fetching tool" });
    }
  });

  // Test endpoint
  app.get("/api/health", (req, res) => {
    console.log("Health check endpoint hit");
    res.json({ 
      status: 'ok',
      timestamp: new Date().toISOString(),
      supabase: !!supabase
    });
  });
}
