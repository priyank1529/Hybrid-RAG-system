# Neo4j Graph Database Setup Guide

## Overview

The system now supports **two graph storage backends**:

1. **SQL-based** (Default) - Uses SQLite/PostgreSQL for graph storage
2. **Neo4j** (Optional) - True graph database with advanced capabilities

## Why Neo4j?

### Benefits of Using Neo4j

✅ **Native Graph Storage**
   - Nodes and relationships stored as first-class citizens
   - No JOIN operations needed for traversals

✅ **Better Performance**
   - Optimized for graph queries
   - Fast multi-hop relationship traversals
   - Efficient pattern matching

✅ **Advanced Graph Algorithms**
   - Shortest path finding
   - Centrality algorithms
   - Community detection
   - PageRank

✅ **Powerful Query Language**
   - Cypher query language
   - Intuitive pattern matching
   - Complex graph queries

✅ **Graph Visualization**
   - Built-in Neo4j Browser
   - Visual graph exploration
   - Interactive query building

## Installation Options

### Option 1: Docker (Recommended)

```bash
# Pull Neo4j image
docker pull neo4j:latest

# Run Neo4j container
docker run \
    -p 7474:7474 -p 7687:7687 \
    -v $HOME/neo4j/data:/data \
    -v $HOME/neo4j/logs:/logs \
    -e NEO4J_AUTH=neo4j/your_password \
    --name neo4j-graphrag \
    neo4j:latest
```

### Option 2: Neo4j Desktop

1. Download from: https://neo4j.com/download/
2. Install Neo4j Desktop
3. Create a new database
4. Start the database
5. Note the connection details

### Option 3: Neo4j Aura (Cloud)

1. Visit: https://neo4j.com/cloud/aura/
2. Create free account
3. Create a new database
4. Copy connection URI and credentials

### Option 4: Local Installation

**Ubuntu/Debian:**
```bash
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
echo 'deb https://debian.neo4j.com stable latest' | sudo tee /etc/apt/sources.list.d/neo4j.list
sudo apt-get update
sudo apt-get install neo4j
sudo systemctl start neo4j
```

**macOS:**
```bash
brew install neo4j
neo4j start
```

## Configuration

### 1. Update .env File

```env
# Neo4j Graph Database
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
USE_NEO4J=true
```

### 2. Verify Connection

Start your application and check the logs:

```bash
python main.py
```

You should see:
```
✅ Neo4j connected successfully
```

If connection fails:
```
⚠️  Neo4j connection failed: <error>
   Falling back to SQL-based graph storage
```

## Using Neo4j

### The system automatically uses Neo4j when available:

1. **Entity Storage**: Entities stored as nodes
2. **Relationship Storage**: Relationships stored as edges
3. **Graph Queries**: Optimized graph traversals
4. **Fallback**: Automatic fallback to SQL if Neo4j unavailable

### No Code Changes Required!

The application automatically detects and uses Neo4j when configured.

## Neo4j Browser

### Access the Browser

1. Open: http://localhost:7474
2. Login with credentials from .env
3. Explore your knowledge graph visually

### Useful Cypher Queries

**View all entities:**
```cypher
MATCH (e:Entity)
RETURN e
LIMIT 50
```

**View entities for a specific user:**
```cypher
MATCH (e:Entity {user_id: 1})
RETURN e
```

**View entities and their relationships:**
```cypher
MATCH (source:Entity)-[r:RELATED]->(target:Entity)
WHERE source.user_id = 1
RETURN source, r, target
LIMIT 100
```

**Find entities by type:**
```cypher
MATCH (e:Entity {type: 'PERSON'})
RETURN e.name, e.description
```

**Find all paths between two entities:**
```cypher
MATCH (e1:Entity {name: 'Alice'})
MATCH (e2:Entity {name: 'Company XYZ'})
MATCH path = (e1)-[*1..5]-(e2)
RETURN path
```

**Find entities related to a concept:**
```cypher
MATCH (e:Entity)-[:RELATED*1..2]-(related:Entity)
WHERE e.name CONTAINS 'Machine Learning'
RETURN e, related
```

**Count entities by type:**
```cypher
MATCH (e:Entity)
RETURN e.type as type, count(*) as count
ORDER BY count DESC
```

**Find most connected entities:**
```cypher
MATCH (e:Entity)-[r]-()
RETURN e.name, e.type, count(r) as connections
ORDER BY connections DESC
LIMIT 10
```

## Data Model in Neo4j

### Node Schema

```
(:Entity {
    id: Integer,
    name: String,
    type: String,
    description: String,
    document_id: Integer,
    user_id: Integer
})
```

### Relationship Schema

```
()-[:RELATED {
    id: Integer,
    type: String,
    description: String
}]->()
```

## Performance Tips

### 1. Create Indexes

```cypher
CREATE INDEX entity_id FOR (e:Entity) ON (e.id);
CREATE INDEX entity_user FOR (e:Entity) ON (e.user_id);
CREATE INDEX entity_document FOR (e:Entity) ON (e.document_id);
CREATE INDEX entity_name FOR (e:Entity) ON (e.name);
```

### 2. Monitor Performance

```cypher
// View active queries
CALL dbms.listQueries();

// View database info
CALL dbms.db.info();
```

### 3. Optimize Memory

Edit `neo4j.conf`:
```
dbms.memory.heap.initial_size=512m
dbms.memory.heap.max_size=1G
dbms.memory.pagecache.size=512m
```

## Comparison: SQL vs Neo4j

### SQL-based Graph Storage

**Pros:**
- ✅ Simple setup (included by default)
- ✅ No additional services required
- ✅ Works with existing database

**Cons:**
- ❌ Slower for complex traversals
- ❌ Requires JOIN operations
- ❌ Limited graph algorithms

**Best for:**
- Getting started quickly
- Small to medium graphs
- Simple relationship queries

### Neo4j Graph Database

**Pros:**
- ✅ Native graph storage
- ✅ Fast graph traversals
- ✅ Advanced graph algorithms
- ✅ Visual graph browser
- ✅ Powerful Cypher queries

**Cons:**
- ❌ Requires separate service
- ❌ Additional configuration
- ❌ Extra memory usage

**Best for:**
- Large knowledge graphs
- Complex relationship queries
- Multi-hop traversals
- Graph analytics

## Migration

### Migrate from SQL to Neo4j

If you've been using SQL-based storage and want to switch to Neo4j:

1. **Enable Neo4j** in .env:
   ```env
   USE_NEO4J=true
   ```

2. **Restart application**:
   ```bash
   python main.py
   ```

3. **Re-process documents** (optional):
   - New documents automatically use Neo4j
   - Existing SQL data remains functional
   - Both can coexist

### Migrate from Neo4j to SQL

1. **Disable Neo4j** in .env:
   ```env
   USE_NEO4J=false
   ```

2. **Restart application**

3. **Data remains in both**:
   - Entities still in SQL database
   - Neo4j data remains but unused

## Troubleshooting

### Connection Failed

**Error:** `Neo4j connection failed`

**Solutions:**
1. Check Neo4j is running: `docker ps` or `neo4j status`
2. Verify credentials in .env
3. Check URI format: `bolt://localhost:7687`
4. Test connection: `curl http://localhost:7474`

### Authentication Error

**Error:** `Authentication failed`

**Solutions:**
1. Reset Neo4j password:
   ```bash
   docker exec neo4j-graphrag neo4j-admin set-initial-password newpassword
   ```
2. Update .env with new password

### Port Already in Use

**Error:** `Port 7687 already in use`

**Solutions:**
1. Stop other Neo4j instances
2. Use different port:
   ```bash
   docker run -p 17687:7687 -p 17474:7474 ...
   ```
3. Update .env: `NEO4J_URI=bolt://localhost:17687`

### Out of Memory

**Error:** `Java heap space`

**Solutions:**
1. Increase Docker memory limit
2. Adjust Neo4j heap size in neo4j.conf
3. Use Neo4j Aura for cloud hosting

## Advanced Features

### 1. Graph Algorithms

The Neo4j service includes:

- **Shortest Path**: Find shortest connection between entities
- **Related Entities**: Multi-hop relationship traversal
- **Graph Statistics**: Count nodes, edges, etc.

```python
# Example: Find shortest path
from src.graphdb.neo4j_service import neo4j_service

path = neo4j_service.find_shortest_path(
    entity1_name="Alice",
    entity2_name="Company XYZ",
    user_id=1
)
```

### 2. Custom Queries

You can add custom Cypher queries in `neo4j_service.py`:

```python
def custom_graph_query(self, user_id: int):
    with self.driver.session() as session:
        result = session.run("""
            MATCH (e:Entity {user_id: $user_id})
            // Your custom Cypher query
            RETURN e
        """, user_id=user_id)
        return [record for record in result]
```

## Production Recommendations

### 1. Security

- Use strong passwords
- Enable SSL/TLS
- Restrict network access
- Use authentication tokens

### 2. Backup

```bash
# Docker backup
docker exec neo4j-graphrag neo4j-admin dump --database=neo4j --to=/backups/neo4j.dump

# Restore
docker exec neo4j-graphrag neo4j-admin load --from=/backups/neo4j.dump --database=neo4j --force
```

### 3. Monitoring

- Enable query logging
- Monitor memory usage
- Track query performance
- Set up alerts

### 4. Scaling

- Use Neo4j Enterprise for clustering
- Consider Neo4j Aura for managed service
- Implement read replicas
- Use causal clustering

## Cost Comparison

### Self-Hosted (Docker)

- **Cost**: Free (compute costs only)
- **Setup**: Medium complexity
- **Maintenance**: You manage
- **Scaling**: Manual

### Neo4j Aura Free

- **Cost**: Free tier available
- **Setup**: Easy (cloud-hosted)
- **Maintenance**: Managed
- **Scaling**: Automatic
- **Limits**: Storage and connections

### Neo4j Aura Professional

- **Cost**: Pay-as-you-go
- **Setup**: Easy
- **Maintenance**: Fully managed
- **Scaling**: Automatic
- **Limits**: Based on tier

## Summary

### Quick Start

1. **Run Neo4j**:
   ```bash
   docker run -p 7474:7474 -p 7687:7687 \
     -e NEO4J_AUTH=neo4j/password \
     neo4j:latest
   ```

2. **Configure .env**:
   ```env
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=password
   USE_NEO4J=true
   ```

3. **Start Application**:
   ```bash
   python main.py
   ```

4. **Verify**:
   - Check logs for "✅ Neo4j connected"
   - Visit http://localhost:7474
   - Upload a document and view in Neo4j Browser

### When to Use Neo4j

**Use Neo4j if:**
- You have large knowledge graphs (>10,000 entities)
- You need complex graph queries
- You want visual graph exploration
- You need graph algorithms
- Performance is critical

**Use SQL if:**
- You're just getting started
- You have simple graphs (<1,000 entities)
- You want minimal setup
- You don't need graph algorithms

Both options work seamlessly - choose based on your needs!
