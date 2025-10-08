# Mappings

A mapping between two vocabularies creates a correspondence or relationship between their terms or concepts. This is often done to enable interoperability, data exchange, or integration between different systems, applications, or domains that use different terminology. 

## Realisation

For PaNET, each mapping to a vocabulary will be handled in a separate csv file. Please use the template to create a new mapping. The csv file will be automatically transformed in a more interoperable ttl file. 

The csv file allows to map terms and concept using the skos terms
- Related Match (symmetric, associative mapping)
- Close Match (symmetric, partially interchangeable)
- Exact Match
- Narrow Match (hierarchical relationship)
- Broad Match (hierarchical relationship)
to facilitate detailed relationships.

If a PaNET term is related to a concept in another vocabulary, then the type of the relationship must be identified. A new line in the csv consists of 
- 1st column: PaNET ID, as panet:PaNETxxxxx
- 2nd column: PaNET name, the label
- in one of the following columns: the unique identifier of the concept of the other vocabulary

## Example

```
ID,Label,Related Match,Close Match,Exact Match,Narrow Match,Broad Match
ID,LABEL,AI skos:relatedMatch SPLIT=|,AI skos:closeMatch SPLIT=|,AI skos:exactMatch SPLIT=|,AI skos:narrowMatch SPLIT=|,AI skos:broadMatch SPLIT=|
panet:PaNET01006,THz photon probe,,,,wfl:6002|wfl:6005,
```
panet:PaNET01006 (THz photon probe) has a narrow matches wfl:6002 (THz spectroscopy) and wfl:6005 (THz high harmonic generatio).


## Some Insights
The first line of the csv are human readable column names. 
The second line consists of ROBOT actionable categories of the columns.
The `wfl:` prefix used in the third line of the example is handled in the makefile and is short for https://www.wayforlight.eu/catalogue?Techniques=
