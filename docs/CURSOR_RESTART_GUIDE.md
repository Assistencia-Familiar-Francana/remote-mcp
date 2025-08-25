# 🔄 Cursor MCP Connection - Restart Guide

## ✅ **Configuration Fixed!**

The MCP configuration has been updated to use absolute paths and a reliable startup script.

### 📁 **Updated Configuration**

**File**: `~/.cursor/mcp.json`
```json
{
  "mcpServers": {
    "remote-ssh": {
      "command": "/home/ramanujan/anaconda3/bin/python",
      "args": ["/home/ramanujan/PP/funeraria/remote-mcp/start_mcp_server.py"],
      "cwd": "/home/ramanujan/PP/funeraria/remote-mcp",
      "env": {
        "MCP_SSH_HOST": "100.65.56.110",
        "MCP_SSH_USER": "abel",
        "MCP_SSH_KEY": "/home/ramanujan/.ssh/id_ed25519",
        "MCP_SSH_PORT": "22",
        "DEBUG": "true",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### 🔄 **How to Restart MCP Connection in Cursor**

1. **In Cursor**: 
   - Click the MCP Tools panel (if open)
   - Toggle the `remote-ssh` server OFF and then ON
   - Or close and reopen Cursor

2. **Alternative**: 
   - Open Command Palette (`Ctrl+Shift+P`)
   - Search for "MCP" commands
   - Restart MCP servers

### ✅ **What Should Happen**

After restarting, you should see:
- ✅ `remote-ssh` server shows as **connected** (green)
- ✅ Shows available tools like `ssh_connect`, `ssh_run`, etc.
- ✅ No more "No tools or prompts" error

### 🧪 **Test It**

Once connected, ask Cursor:
```
"Connect to my Kubernetes cluster and show me the current system status"
```

### 🔧 **If Still Not Working**

1. **Check the startup script manually**:
   ```bash
   cd /home/ramanujan/PP/funeraria/remote-mcp
   python start_mcp_server.py
   ```

2. **Check Cursor logs**:
   - Look for MCP connection logs in Cursor
   - Should show successful connection instead of ModuleNotFoundError

3. **Restart Cursor completely**:
   - Close Cursor entirely
   - Reopen and check MCP Tools panel

---

## 🎯 **Expected Result**

After restart, your MCP Tools panel should show:
- ✅ `remote-ssh` server (green/connected)
- ✅ Available tools: `ssh_connect`, `ssh_run`, `ssh_disconnect`, `ssh_list_sessions`

Then you can start using natural language to manage your Kubernetes infrastructure! 🚀
