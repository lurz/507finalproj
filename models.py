
class Track:
    def __init__(self, data=None):
        super().__init__()
        item = data['tracks']['items'][0]
        self.id = item['id']
        self.name = item['name']
        self.popularity = item['popularity']
        self.minute = int((int(item['duration_ms'])/(1000*60))%60)
        self.second = int((int(item['duration_ms'])/1000)%60)
        if self.second < 10:
            self.second = '0' + str(self.second)
        else:
            self.second = str(self.second)
        self.explicit = bool(item['explicit'])
        self.album = item['album']['name']
        self.img_src = item['album']['images'][2]['url']
        self.next = data['tracks']['next']
        self.prev = data['tracks']['previous']

    def present(self):
        context = {}
        context['id'] = self.id
        context['name'] = self.name 
        context['popularity'] = self.popularity
        context['minute'] = self.minute
        context['second'] = self.second
        context['explicit'] = self.explicit
        context['album'] = self.album
        context['img_src'] = self.img_src
        context['lyrics'] = self.lyrics
        context['next'] = self.next
        context['prev'] = self.prev
        return context


class Artist:
    def __init__(self, data=None):
        super().__init__()
        self.id  = data['id']
        self.img_src = data['images'][2]['url']
        self.name = data['name']
        if len(data['genres']) > 3:
            self.genres = data['genres'][0:3]
        else:
            self.genres = data['genres']
        self.popularity = data['popularity']

    def present(self):
        context = {}
        context['id'] = self.id
        context['name'] = self.name 
        context['popularity'] = self.popularity
        context['img_src'] = self.img_src
        context['genres'] = self.genres
        return context


class Recommendation:
    def __init__(self, item=None, img_src=None):
        super().__init__()
        self.id = item['id']
        self.name = item['name']
        self.minute = int((int(item['duration_ms'])/(1000*60))%60)
        self.second = int((int(item['duration_ms'])/1000)%60)
        if self.second < 10:
            self.second = '0' + str(self.second)
        else:
            self.second = str(self.second)
        self.explicit = bool(item['explicit'])
        self.artists = []
        self.img_src = img_src
        for artist in item['artists']:
            self.artists.append(artist['name'])
        self.url = f'/search?artist={self.artists[0]}&track={self.name}'

    def present(self):
        context = {}
        context['id'] = self.id
        context['name'] = self.name 
        context['minute'] = self.minute
        context['second'] = self.second
        context['explicit'] = self.explicit
        context['artists'] = self.artists
        context['img_src'] = self.img_src
        context['url'] = self.url
        return context
