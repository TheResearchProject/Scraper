from scrapy.item import Item, Field

class Article(Item):
    title = Field()
    url = Field()
    
    author = Field()
    
    date = Field()
    views = Field()
    
    lead = Field()
    text = Field()
    
    comments = Field()
    images = Field()
    twitter = Field()
    facebook = Field()
    googleplus = Field()
    pinit = Field()

class Image(Item):
    imageurl = Field()
    imagename = Field()
    position = Field()

class Comment(Item):
    id = Field()
    parent_id = Field()
    
    author = Field()
    
    date = Field()
    score = Field()
    content = Field()
    likes = Field()

class Author(Item):
    id = Field()
    type = Field()
    date_scraped = Field()
    
    name = Field()
    bio = Field()
    
    profiel = Field()
    statistieken = Field()
    status = Field()
    tweaker_cv = Field()