platform 2 platform
===================

This project is part of Institute of Network Cultures' [Making Public](http://networkcultures.org/makingpublic/) project.

We're building an article suggestion system, by indexing in a common database the articles of the three online journals taking part in the project. We're doing this by mixing algorithmic suggestions combined with human editorial choice.

Whenever you're reading an article from Journal 1, you'll get suggestions (in the form of online ads) from Journal 2 and 3. Suggestions are based on article topic, title, author, keywoards and text analysis.

We're re-creating a web-ring on a bigger-scale.

## Diagram

1. python scraper(s)
2. python text processing
3. data saved to postgresql database
4. javascript script embedded in each journal website, to talk between journal and database
