# Graph Storage: SQL vs Neo4j

## Overview

The Graph RAG system now supports **two graph storage backends**, giving you flexibility based on your needs and scale.

## Storage Options

### 1. SQL-Based Graph Storage (Default)

**Technology**: SQLite/PostgreSQL with junction tables

**How it works:**
- Entities stored in `entities` table
- Relationships stored in `relationships` table
- Graph traversal uses SQL JOINs

**Data Model:**
```sql
entities (id, name, type, description, document_id)
relationships (id, source_id, target_id, type, description)
```

**Pros:**
- ✅ Zero additional setup
- ✅ Included by default
- ✅ Uses existing database
- ✅ Simple to understand
- ✅ Works for small-medium graphs

**Cons:**
- ❌ Slower for deep traversals
- ❌ Requires multiple JOINs
- ❌ Limited graph algorithms
- ❌ Not optimized for graph queries

**Best for:**
- Getting started quickly
- Small graphs (<5,000 entities)
- Simple relationship queries
- Development and testing

### 2. Neo4j Graph Database (Optional)

**Technology**: Native graph database with Cypher query language

**How it works:**
- Entities as graph nodes
- Relationships as graph edges
- Native graph traversal (no JOINs)

**Data Model:**
```cypher
(:Entity {id, name, type, description, document_id, user_id})
-[:RELATED {id, type, description}]->
(:Entity)
```

**Pros:**
- ✅ Native graph storage
- ✅ Fast multi-hop traversals
- ✅ Advanced graph algorithms
- ✅ Visual graph browser
- ✅ Powerful Cypher queries
- ✅ Scales to millions of nodes

**Cons:**
- ❌ Requires separate service
- ❌ Additional configuration
- ❌ More memory usage
- ❌ Learning curve for Cypher

**Best for:**
- Large knowledge graphs (>10,000 entities)
- Complex graph queries
- Multi-hop relationship discovery
- Graph analytics and algorithms
- Production deployments

## Performance Comparison

### Query: Find all entities 2-hops away from "Machine Learning"

**SQL-Based (2 levels of JOINs):**
```sql
SELECT DISTINCT e3.*
FROM entities e1
JOIN relationships r1 ON e1.id = r1.source_id
JOIN entities e2 ON r1.target_id = e2.id
JOIN relationships r2 ON e2.id = r2.source_id
JOIN entities e3 ON r2.target_id = e3.id
WHERE e1.name LIKE '%Machine Learning%'
```
**Time**: ~500-1000ms for 1,000 entities

**Neo4j (Native traversal):**
```cypher
MATCH (e:Entity)-[:RELATED*1..2]-(related:Entity)
WHERE e.name CONTAINS 'Machine Learning'
RETURN DISTINCT related
```
**Time**: ~50-100ms for 1,000 entities

**Result**: Neo4j is **5-10x faster** for graph traversals

### Query: Shortest path between two entities

**SQL-Based:**
- Requires recursive CTEs or multiple queries
- Performance degrades exponentially
- Complex to implement

**Neo4j:**
```cypher
MATCH path = shortestPath((e1)-[:RELATED*]-(e2))
WHERE e1.name = 'Alice' AND e2.name = 'Bob'
RETURN path
```
- Built-in algorithm
- Optimized performance
- Simple query

## Feature Comparison

| Feature | SQL | Neo4j |
|---------|-----|-------|
| **Setup** | ✅ Immediate | ⚠️ Requires service |
| **1-hop queries** | ✅ Fast | ✅ Fast |
| **Multi-hop queries** | ❌ Slow | ✅ Fast |
| **Shortest path** | ❌ Complex | ✅ Built-in |
| **Graph algorithms** | ❌ Limited | ✅ Extensive |
| **Visual exploration** | ❌ None | ✅ Neo4j Browser |
| **Query language** | SQL | Cypher |
| **Scalability** | ~1-5K entities | Millions |
| **Memory usage** | Low | Medium-High |
| **Cost** | Free | Free-Paid |

## Switching Between Backends

### The system uses **automatic fallback**:

```python
# Application automatically detects Neo4j availability
if neo4j_service.is_available():
    # Use Neo4j for better performance
    return neo4j_service.get_user_graph(user_id)
else:
    # Fallback to SQL-based storage
    return sql_based_graph(user_id)
```

### Dual Storage

Both backends store data simultaneously when Neo4j is enabled:

1. **SQL Database** - Always stores entities/relationships
2. **Neo4j** - Also stores when `USE_NEO4J=true`

**Benefits:**
- Data redundancy
- Can switch backends anytime
- SQL for metadata queries
- Neo4j for graph queries

## Use Cases

### Use SQL-Based When:

1. **Prototyping**: Quick start without extra setup
2. **Small Scale**: <1,000 entities
3. **Simple Queries**: Direct relationships only
4. **Resource Constrained**: Limited memory/CPU
5. **Learning**: Understanding the basics

**Example Scenarios:**
- Personal knowledge base
- Small team documentation
- Development environment
- Learning Graph RAG concepts

### Use Neo4j When:

1. **Large Scale**: >10,000 entities
2. **Complex Queries**: Multi-hop traversals
3. **Graph Analytics**: Need algorithms
4. **Performance Critical**: Fast response required
5. **Production**: Scaling for users

**Example Scenarios:**
- Enterprise knowledge management
- Research paper analysis
- Customer relationship mapping
- Fraud detection
- Network analysis

## Migration Path

### Start with SQL → Move to Neo4j

**Phase 1: Development (SQL)**
```env
USE_NEO4J=false
```
- Quick development
- No extra setup
- Proof of concept

**Phase 2: Testing (Dual)**
```env
USE_NEO4J=true
```
- Install Neo4j
- Both systems active
- Compare performance

**Phase 3: Production (Neo4j)**
```env
USE_NEO4J=true
```
- Neo4j primary
- SQL as backup
- Optimized queries

## Cost Analysis

### SQL-Based (SQLite)

**Setup Cost**: $0
**Hosting**: Included with app
**Scaling**: Vertical (bigger server)
**Total**: **Free**

### Neo4j Options

**Option 1: Docker (Self-Hosted)**
- Setup: Free
- Hosting: Compute costs only
- Scaling: Manual
- Total: **~$10-50/month** (server costs)

**Option 2: Neo4j Aura Free**
- Setup: Free
- Hosting: Managed
- Limits: 50MB, 200K nodes
- Total: **Free** (with limits)

**Option 3: Neo4j Aura Pro**
- Setup: Free
- Hosting: Managed
- Scaling: Automatic
- Total: **~$65-500/month** (based on usage)

## Best Practices

### For SQL-Based

1. **Index key columns**: `user_id`, `document_id`, `name`
2. **Limit depth**: Avoid >2 hop queries
3. **Cache results**: Store frequent queries
4. **Batch operations**: Insert entities in batches

### For Neo4j

1. **Create indexes**: On `id`, `user_id`, `document_id`
2. **Use constraints**: Unique constraints on IDs
3. **Optimize queries**: Use PROFILE to analyze
4. **Monitor memory**: Adjust heap size as needed
5. **Regular backups**: Schedule automated backups

## Decision Matrix

| Your Situation | Recommendation |
|----------------|---------------|
| Just starting | **SQL** - Learn basics first |
| <1K entities | **SQL** - Sufficient performance |
| 1K-10K entities | **Either** - Depends on query complexity |
| >10K entities | **Neo4j** - Better performance |
| Complex queries | **Neo4j** - Native graph operations |
| Simple queries | **SQL** - Easier to understand |
| Limited budget | **SQL** - No extra costs |
| Production scale | **Neo4j** - Enterprise features |
| Need algorithms | **Neo4j** - Built-in graph algorithms |
| Visual exploration | **Neo4j** - Graph browser included |

## Getting Started

### With SQL (Already configured!)

No additional setup needed. Just run:
```bash
python main.py
```

### With Neo4j

1. **Install Neo4j** (see [NEO4J_SETUP.md](NEO4J_SETUP.md)):
   ```bash
   docker run -p 7474:7474 -p 7687:7687 \
     -e NEO4J_AUTH=neo4j/password \
     neo4j:latest
   ```

2. **Enable in .env**:
   ```env
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=password
   USE_NEO4J=true
   ```

3. **Start application**:
   ```bash
   python main.py
   ```

4. **Verify**:
   - Check logs: "✅ Neo4j connected"
   - Browse: http://localhost:7474

## Summary

**TL;DR:**

- **SQL**: Great for getting started, simple setup, works well for small-medium graphs
- **Neo4j**: Powerful for large graphs, complex queries, production deployments
- **Both**: Can coexist, automatic fallback, switch anytime

**Recommendation:**
1. Start with SQL (already configured)
2. Upload documents and test features
3. If you need better performance or have >5K entities, add Neo4j
4. Both options work seamlessly!

Choose based on your current needs - you can always upgrade later! 🚀
