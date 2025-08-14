/**
 * Node.js MCP SSH Server - Alternative implementation using ssh2
 * This is a minimal example showing how to implement the same functionality in Node.js
 */

import { Client } from 'ssh2';
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';

interface SSHSession {
  id: string;
  client: Client;
  connected: boolean;
  host: string;
  username: string;
  lastUsed: Date;
}

class NodeSSHMCPServer {
  private server: Server;
  private sessions: Map<string, SSHSession> = new Map();
  
  // Security allowlist (subset for demo)
  private allowedCommands = [
    'ls', 'cat', 'head', 'tail', 'grep', 'find', 'pwd', 'whoami',
    'kubectl', 'docker', 'systemctl', 'journalctl', 'uname', 'date'
  ];

  constructor() {
    this.server = new Server(
      { name: 'node-ssh-mcp', version: '0.1.0' },
      { capabilities: { tools: {} } }
    );

    this.setupHandlers();
  }

  private setupHandlers() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: 'ssh_connect',
          description: 'Connect to SSH server',
          inputSchema: {
            type: 'object',
            properties: {
              host: { type: 'string' },
              port: { type: 'number', default: 22 },
              username: { type: 'string' },
              password: { type: 'string' },
              session_id: { type: 'string' }
            },
            required: ['host', 'username']
          }
        },
        {
          name: 'ssh_run',
          description: 'Execute command via SSH',
          inputSchema: {
            type: 'object',
            properties: {
              session_id: { type: 'string' },
              cmd: { type: 'string' },
              timeout_ms: { type: 'number', default: 30000 }
            },
            required: ['session_id', 'cmd']
          }
        },
        {
          name: 'ssh_disconnect',
          description: 'Disconnect SSH session',
          inputSchema: {
            type: 'object',
            properties: {
              session_id: { type: 'string' }
            },
            required: ['session_id']
          }
        }
      ]
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case 'ssh_connect':
            return await this.handleConnect(args);
          case 'ssh_run':
            return await this.handleRun(args);
          case 'ssh_disconnect':
            return await this.handleDisconnect(args);
          default:
            throw new Error(`Unknown tool: ${name}`);
        }
      } catch (error) {
        return {
          content: [{
            type: 'text',
            text: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`
          }]
        };
      }
    });
  }

  private async handleConnect(args: any) {
    const { host, port = 22, username, password, session_id } = args;
    const sessionId = session_id || Math.random().toString(36).substr(2, 9);

    return new Promise((resolve) => {
      const client = new Client();
      
      client.on('ready', () => {
        const session: SSHSession = {
          id: sessionId,
          client,
          connected: true,
          host,
          username,
          lastUsed: new Date()
        };
        
        this.sessions.set(sessionId, session);
        
        resolve({
          content: [{
            type: 'text',
            text: JSON.stringify({
              success: true,
              session_id: sessionId,
              message: `Connected to ${username}@${host}:${port}`
            }, null, 2)
          }]
        });
      });

      client.on('error', (err) => {
        resolve({
          content: [{
            type: 'text', 
            text: JSON.stringify({
              success: false,
              error: `Connection failed: ${err.message}`
            }, null, 2)
          }]
        });
      });

      client.connect({
        host,
        port,
        username,
        password,
        readyTimeout: 30000
      });
    });
  }

  private async handleRun(args: any) {
    const { session_id, cmd, timeout_ms = 30000 } = args;
    
    const session = this.sessions.get(session_id);
    if (!session || !session.connected) {
      return {
        content: [{
          type: 'text',
          text: JSON.stringify({
            success: false,
            error: `Session '${session_id}' not found or not connected`
          }, null, 2)
        }]
      };
    }

    // Validate command
    const cmdParts = cmd.trim().split(/\s+/);
    const cmdName = cmdParts[0];
    
    if (!this.allowedCommands.includes(cmdName)) {
      return {
        content: [{
          type: 'text',
          text: JSON.stringify({
            success: false,
            error: `Command '${cmdName}' not allowed`
          }, null, 2)
        }]
      };
    }

    return new Promise((resolve) => {
      session.client.exec(cmd, { pty: false }, (err, stream) => {
        if (err) {
          resolve({
            content: [{
              type: 'text',
              text: JSON.stringify({
                success: false,
                error: `Execution failed: ${err.message}`
              }, null, 2)
            }]
          });
          return;
        }

        let stdout = '';
        let stderr = '';
        const startTime = Date.now();
        
        // Set timeout
        const timer = setTimeout(() => {
          stream.destroy();
          resolve({
            content: [{
              type: 'text',
              text: JSON.stringify({
                success: false,
                error: 'Command timeout',
                duration_ms: Date.now() - startTime
              }, null, 2)
            }]
          });
        }, timeout_ms);

        stream.on('close', (code: number) => {
          clearTimeout(timer);
          session.lastUsed = new Date();
          
          resolve({
            content: [{
              type: 'text',
              text: JSON.stringify({
                success: true,
                session_id,
                stdout: stdout.trim(),
                stderr: stderr.trim(),
                exit_status: code,
                duration_ms: Date.now() - startTime
              }, null, 2)
            }]
          });
        });

        stream.on('data', (data: Buffer) => {
          stdout += data.toString();
          
          // Limit output size (128KB)
          if (stdout.length > 128 * 1024) {
            stream.destroy();
            clearTimeout(timer);
            
            resolve({
              content: [{
                type: 'text',
                text: JSON.stringify({
                  success: true,
                  session_id,
                  stdout: stdout.substring(0, 128 * 1024) + '\\n[OUTPUT TRUNCATED]',
                  stderr,
                  exit_status: null,
                  duration_ms: Date.now() - startTime,
                  truncated: true
                }, null, 2)
              }]
            });
          }
        });

        stream.stderr.on('data', (data: Buffer) => {
          stderr += data.toString();
        });
      });
    });
  }

  private async handleDisconnect(args: any) {
    const { session_id } = args;
    
    const session = this.sessions.get(session_id);
    if (session) {
      session.client.end();
      this.sessions.delete(session_id);
      
      return {
        content: [{
          type: 'text',
          text: JSON.stringify({
            success: true,
            message: `Session '${session_id}' disconnected`
          }, null, 2)
        }]
      };
    }
    
    return {
      content: [{
        type: 'text',
        text: JSON.stringify({
          success: false,
          error: `Session '${session_id}' not found`
        }, null, 2)
      }]
    };
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Node SSH MCP Server running on stdio');
  }
}

// Start server
const server = new NodeSSHMCPServer();
server.run().catch(console.error);

export default NodeSSHMCPServer;
