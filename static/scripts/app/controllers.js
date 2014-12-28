var mach2Controllers = angular.module(
  'mach2Controllers',
  [
    'ui.bootstrap',
    'angularMoment'
  ]
);

mach2Controllers.controller('NavCtrl', ['$scope', function($scope) {
}]);

mach2Controllers.controller(
  'ArtistCtrl',
  [
    '$scope',
    'ArtistSearch',
    function($scope, ArtistSearch) {
      $scope.totalArtists  = ArtistSearch.query();
      $scope.indices       = [
        'A',
        'B',
        'C',
        'D',
        'E',
        'F',
        'G',
        'H',
        'I',
        'J',
        'K',
        'L',
        'M',
        'N',
        'O',
        'P',
        'Q',
        'R',
        'S',
        'T',
        'U',
        'V',
        'W',
        'X',
        'Y',
        'Z',
        '0-9',
        'Other'
      ];
      $scope.selectedIndex = $scope.indices[0];
    }
  ]
);

mach2Controllers.controller(
  'ArtistDetailCtrl',
  [
    '$scope',
    '$stateParams',
    'Artist',
    'ArtistAlbums',
    'ArtistTracks',
    function(
      $scope,
      $stateParams,
      Artist,
      ArtistAlbums,
      ArtistTracks
    ) {
      console.log('Am I here?');
      $scope.artist = Artist.query({
        artistId: $stateParams.artistId
      });

      $scope.albums = ArtistAlbums.query({
        artistId: $stateParams.artistId
      });

      $scope.tracks = ArtistTracks.query({
        artistId: $stateParams.artistId
      });
    }
  ]
);

mach2Controllers.controller(
  'ArtistTracksCtrl',
  [
    '$scope',
    '$stateParams',
    'Artist',
    'ArtistTracks',
    function($scope, $stateParams, Artist, ArtistTracks) {
      $scope.artist = Artist.query({
        artistId: $stateParams.artistId
      });

      $scope.tracks = ArtistTracks.query({
        artistId: $stateParams.artistId
      });
    }
  ]
);

mach2Controllers.controller(
  'AlbumCtrl',
  [
    '$scope',
    'AlbumArtists',
    'AlbumSearch',
    function($scope, AlbumArtists, AlbumSearch) {
      // horrible way of calculating decades
      var currentYear = moment().format('YYYY');
      var startDecade = 1940;

      var decades = [];

      for (i = (startDecade/10); i <= (currentYear/10); i++) {
        decades.push(i * 10);
      }

      $scope.albums        = AlbumSearch.query();
      $scope.indices       = decades;
      $scope.selectedIndex = $scope.indices[0];
      $scope.albumArtists  = AlbumArtists;
    }
  ]
);

mach2Controllers.controller(
  'AlbumDetailCtrl',
  [
    '$scope',
    '$stateParams',
    'Album',
    'AlbumTracks',
    function(
      $scope,
      $stateParams,
      Album,
      AlbumTracks
    ) {

    }
  ]
);

mach2Controllers.controller('TrackCtrl', ['$scope', function($scope) {
}]);
