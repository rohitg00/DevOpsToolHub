import express from 'express';
import { supabase } from '../db';
import fetch from 'node-fetch';
import { Tool } from '../db/schema';

const router = express.Router();

// Get all tools
router.get('/', async (req, res) => {
  console.log('GET /api/tools - Fetching all tools...');
  try {
    // Set cache control headers
    res.set('Cache-Control', 'no-store, no-cache, must-revalidate, private');
    res.set('Expires', '-1');
    res.set('Pragma', 'no-cache');

    let allTools: Tool[] = [];
    let page = 0;
    const pageSize = 1000;
    
    // Fetch tools in batches
    while (true) {
      const { data: tools, error } = await supabase
        .from('tools')
        .select('*')
        .order('upvotes', { ascending: false })
        .range(page * pageSize, (page + 1) * pageSize - 1);

      if (error) {
        console.error('Supabase error:', error);
        throw error;
      }

      if (!tools || tools.length === 0) break;
      
      allTools = [...allTools, ...tools];
      console.log(`Fetched page ${page + 1}, got ${tools.length} tools`);
      
      if (tools.length < pageSize) break;
      page++;
    }

    // Log unique categories for debugging
    const uniqueCategories = new Set(allTools?.map(t => t.category));
    console.log('Available categories:', Array.from(uniqueCategories));
    console.log(`Total tools found: ${allTools.length}`);

    // Fetch READMEs in parallel for tools with GitHub URLs
    const toolsWithReadme = await Promise.all(
      allTools.map(async (tool) => {
        if (!tool.githubUrl) return tool;

        try {
          const githubPath = new URL(tool.githubUrl).pathname.slice(1);
          const readmeUrl = `https://raw.githubusercontent.com/${githubPath}/main/README.md`;
          console.log(`Fetching README for ${tool.name} from: ${readmeUrl}`);
          
          const readmeResponse = await fetch(readmeUrl);
          
          if (readmeResponse.ok) {
            const readme = await readmeResponse.text();
            return { ...tool, readme };
          }

          // Try master branch if main doesn't exist
          const masterReadmeUrl = `https://raw.githubusercontent.com/${githubPath}/master/README.md`;
          console.log(`Trying master branch for ${tool.name}: ${masterReadmeUrl}`);
          const masterReadmeResponse = await fetch(masterReadmeUrl);
          
          if (masterReadmeResponse.ok) {
            const readme = await masterReadmeResponse.text();
            return { ...tool, readme };
          }

          console.log(`No README found for ${tool.name}`);
          return tool;
        } catch (readmeError) {
          console.error(`Error fetching README for ${tool.name}:`, readmeError);
          return tool;
        }
      })
    );

    console.log(`Found ${toolsWithReadme.length} tools (with READMEs where available)`);
    res.json(toolsWithReadme);
  } catch (error) {
    console.error('Error fetching tools:', error);
    res.status(500).json({ message: 'Error fetching tools' });
  }
});

// Check upvote status
router.head('/:name/upvote', async (req, res) => {
  const { name } = req.params;
  const clientIp = req.ip;

  try {
    const { data, error } = await supabase
      .from('tool_upvote_tracking')
      .select('*')
      .eq('tool_name', name)
      .eq('ip_address', clientIp)
      .single();

    if (error && error.code !== 'PGRST116') {
      console.error('Error checking upvote status:', error);
      res.status(500).end();
      return;
    }

    res.status(data ? 200 : 404).end();
  } catch (error) {
    console.error('Error checking upvote status:', error);
    res.status(500).end();
  }
});

// Upvote a tool
router.post('/:name/upvote', async (req, res) => {
  const { name } = req.params;
  const clientIp = req.ip;

  console.log(`POST /api/tools/${name}/upvote - Managing upvote from ${clientIp}`);

  try {
    const { data, error } = await supabase.rpc('handle_upvote', {
      p_tool_name: name,
      p_ip_address: clientIp
    });

    if (error) {
      console.error('Error managing upvote:', error);
      throw error;
    }

    console.log('Upvote result:', data);
    res.json(data);
  } catch (error: any) {
    console.error('Error managing upvote:', error);
    if (error.code === '23505') {
      res.json({ 
        action: 'unchanged',
        message: 'Already upvoted'
      });
    } else {
      res.status(500).json({ 
        message: 'Error managing upvote',
        error: String(error)
      });
    }
  }
});

// Get a specific tool
router.get('/:name', async (req, res) => {
  const { name } = req.params;

  console.log(`GET /api/tools/${name} - Fetching tool details...`);
  try {
    const { data: tool, error } = await supabase
      .from('tools')
      .select('*')
      .eq('name', name)
      .single();

    if (error) throw error;
    if (!tool) {
      return res.status(404).json({ message: 'Tool not found' });
    }

    console.log('Tool data from DB:', tool);

    // If there's a GitHub URL, fetch the README
    if (tool.githubUrl) {
      console.log(`Found GitHub URL: ${tool.githubUrl}`);
      try {
        const githubUrl = new URL(tool.githubUrl);
        const [owner, repo] = githubUrl.pathname.slice(1).split('/');
        console.log(`Owner: ${owner}, Repo: ${repo}`);
        
        const readmeVariations = [
          `https://raw.githubusercontent.com/${owner}/${repo}/main/README.md`,
          `https://raw.githubusercontent.com/${owner}/${repo}/master/README.md`,
          `https://raw.githubusercontent.com/${owner}/${repo}/main/readme.md`,
          `https://raw.githubusercontent.com/${owner}/${repo}/master/readme.md`
        ];

        for (const readmeUrl of readmeVariations) {
          console.log(`Attempting to fetch README from: ${readmeUrl}`);
          const readmeResponse = await fetch(readmeUrl);
          console.log(`Response status: ${readmeResponse.status}`);
          
          if (readmeResponse.ok) {
            const readme = await readmeResponse.text();
            if (readme.trim()) {
              console.log(`Found README content (length: ${readme.length})`);
              tool.readme = readme;
              break;
            } else {
              console.log('README content was empty');
            }
          }
        }

        if (!tool.readme) {
          console.log('No valid README found after trying all variations');
        }
      } catch (readmeError) {
        console.error('Error fetching README:', readmeError);
      }
    } else {
      console.log('No GitHub URL found for tool');
    }

    console.log(`Sending response for ${name}${tool.readme ? ' (with README)' : ' (no README)'}`);
    res.json(tool);
  } catch (error) {
    console.error('Error fetching tool:', error);
    res.status(500).json({ message: 'Error fetching tool', error: String(error) });
  }
});

export default router; 