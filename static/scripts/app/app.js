var mach2App = angular.module(
  'mach2App',
  [
    'ui.router',
    'mach2Services',
    'mach2Controllers',
    'mach2Filters',
    'ui.bootstrap',
    'angularMoment'
  ]
);

mach2App.config(
  [
    '$stateProvider',
    '$urlRouterProvider',
    function($stateProvider, $urlRouterProvider) {
      $stateProvider.state('artists', {
        url:         '/artists',
        templateUrl: 'static/partials/artists/list.html',
        controller:  'ArtistCtrl',
      });

      $stateProvider.state('artistdetail', {
        url:         '/artists/{artistId:int}',
        templateUrl: 'static/partials/artists/detail.html',
        controller:  'ArtistDetailCtrl',
        resolve:     {
          artistId: ['$stateParams', function($stateParams) {
            return $stateParams.artistId;
          }]
        },
      });

      $stateProvider.state('artistdetail.tracks', {
        url:         '/tracks',
        templateUrl: 'static/partials/artists/tracks.html',
        controller:  'ArtistTracksCtrl'
      });

      $stateProvider.state('albums', {
        url:         '/albums',
        templateUrl: 'static/partials/albums/list.html',
        controller:  'AlbumCtrl'
      });

      $stateProvider.state('albums.detail', {
        url:         '/{albumId:int}',
        templateUrl: 'static/partials/album/detail.html',
        controller:  'AlbumDetailCtrl'
      });

      $urlRouterProvider.otherwise('/artists');
    }
  ]
);

mach2App.constant(
  'angularMomentConfig',
  {
    timezone: 'utc'
  }
);