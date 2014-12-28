var mach2Services = angular.module('mach2Services', ['ngResource']);

mach2Services.factory('Artist', ['$resource', function($resource) {
  return $resource('artists/:artistId', {}, {
    query:  {
      method: 'GET'
    }
  });
}]);

mach2Services.factory('ArtistAlbums', ['$resource', function($resource) {
  return $resource('artists/:artistId/albums', {}, {
    query:  {
      method:  'GET',
      isArray: true
    }
  });
}]);

mach2Services.factory('ArtistSearch', ['$resource', function($resource) {
  return $resource('artists/:name', {}, {
    query:  {
      method:  'GET',
      isArray: true
    }
  });
}]);

mach2Services.factory('ArtistTracks', ['$resource', function($resource) {
  return $resource('artists/:artistId/tracks', {}, {
    query:  {
      method:  'GET',
      isArray: true
    }
  });
}]);

mach2Services.factory('Album', ['$resource', function($resource) {
  return $resource('albums/:albumId', {}, {
    query:  {
      method: 'GET'
    }
  });
}]);

mach2Services.factory('AlbumArtists', ['$resource', function($resource) {
  return $resource('albums/:albumId/artists', {}, {
    query:  {
      method:  'GET',
      isArray: true
    }
  });
}]);

mach2Services.factory('AlbumSearch', ['$resource', function($resource) {
  return $resource('albums/:name', {}, {
    query:  {
      method:  'GET',
      isArray: true,
    }
  });
}]);

mach2Services.factory('AlbumTracks', ['$resource', function($resource) {
  return $resource('albums/:albumId/tracks', {}, {
    query:  {
      method:  'GET',
      isArray: true
    }
  });
}]);

mach2Services.factory('Track', ['$resource', function($resource) {
  return $resource('tracks/:trackId', {}, {
    query:  {
      method: 'GET'
    }
  });
}]);

mach2Services.factory('TrackArtists', ['$resource', function($resource) {
  return $resource('tracks/:trackId/artists', {}, {
    query:  {
      method: 'GET'
    }
  });
}]);


mach2Services.factory('TrackSearch', ['$resource', function($resource) {
  return $resource('tracks/:name', {}, {
    query:  {
      method:  'GET',
      isArray: true
    }
  });
}]);
