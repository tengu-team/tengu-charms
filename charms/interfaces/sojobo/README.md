# Sojobo-API Interface

This is a Juju charm interface layer. This interface is used for exchanging certain details of the Sojobo-API.

## States

**{relation_name}.available** - Denotes that the client has connected and received all the information from the provider to make the connection.

**{relation_name}.removed** - Denotes that the unit has departed from the relationship, and should be removed from any configuration files, etc.

## Data

- **url** - The Full Qualified Domain Name of the Sojobo-API
- **api-dir** - The root dir of the API
- **api-key** - The api-key used to make calls to the API
- **user** - As which user the API is running

## Usage

`metadata.yaml`

```yaml
requires:
  sojobo:
    interface: sojobo
```

`layer.yaml`

```yaml
includes: ['interface:sojobo']
```  

`reactive/code.py`

```python
@when('sojobo.available')
def example(sojobo):
    print(sojobo.connection())
```
