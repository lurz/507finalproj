
class Track:
    def __init__(self, data=None, db=None):
        super().__init__()
        if data:
            item = data['tracks']['items'][0]
            self.id = item['id']
            self.name = item['name']
            self.popularity = item['popularity']
            self.minute = int((int(item['duration_ms']) / (1000 * 60)) % 60)
            self.second = int((int(item['duration_ms']) / 1000) % 60)
            if self.second < 10:
                self.second = '0' + str(self.second)
            else:
                self.second = str(self.second)
            self.explicit = bool(item['explicit'])
            self.album = item['album']['name']
            self.img_src = item['album']['images'][2]['url']
            self.lyrics = ''
            return
        if db:
            self.id = db['id']
            self.name = db['trackname']
            self.popularity = db['popularity']
            self.minute = db['minute']
            self.second = db['second']
            self.explicit = bool(db['ifexplicit'])
            self.album = db['albumname']
            self.img_src = db['imgsrc']
            self.lyrics = db['lyrics']
            return

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
        return context

    def db_tuple(self):
        return (self.id, self.name, self.popularity, str(self.minute), self.second, int(
            self.explicit), self.album, self.img_src, self.lyrics)


class Artist:
    def __init__(self, data=None, db=None):
        super().__init__()
        if data:
            self.id = data['id']
            self.img_src = data['images'][2]['url']
            self.name = data['name']
            if len(data['genres']) > 3:
                self.genres = data['genres'][0:3]
            else:
                self.genres = data['genres']
            self.popularity = data['popularity']
            return
        if db:
            self.id = db['id']
            self.img_src = db['imgsrc']
            self.name = db['artistname']
            self.genres = db['genres'].split(',')
            self.popularity = db['popularity']

    def present(self):
        context = {}
        context['id'] = self.id
        context['name'] = self.name
        context['popularity'] = self.popularity
        context['img_src'] = self.img_src
        context['genres'] = self.genres
        return context

    def db_tuple(self):
        return (self.id, self.name, self.popularity,  self.img_src, (',').join(self.genres), )


class Recommendation:
    def __init__(self, item=None, img_src=None, db=None):
        super().__init__()
        if not db:
            self.id = item['id']
            self.name = item['name']
            self.minute = int((int(item['duration_ms']) / (1000 * 60)) % 60)
            self.second = int((int(item['duration_ms']) / 1000) % 60)
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
        else:
            self.id = db['id']
            self.name = db['trackname']
            self.minute = db['minute']
            self.second = db['second']
            self.explicit = bool(db['ifexplicit'])
            self.artists = db['artists'].split(',')
            self.img_src = db['imgsrc']
            self.url = db['urltrack']

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

    def db_tuple(self, trackid):
        return (self.id, trackid, self.name, str(self.minute), self.second, int(
            self.explicit), self.img_src, (',').join(self.artists), self.url, )

