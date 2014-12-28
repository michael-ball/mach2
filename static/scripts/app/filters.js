var mach2Filters = angular.module('mach2Filters',[]);

mach2Filters.filter('alphabetFilter', function() {
  return function(items, search) {
    if (!search) {
      return items;
    }

    return items.filter(function(element, index, array) {
      var searchTerm  = search.param;
      var searchAttrs = search.attrs;
      var regexp      = new RegExp(searchTerm, 'i');

      var searchString = null;

      for(i = 0; i < searchAttrs.length; i++) {
        if (element[searchAttrs[i]]) {
          searchString = element[searchAttrs[i]];
          break;
        }
      }

      if (searchTerm === '0-9') {
        regexp = /[0-9]/;
      } else if (searchTerm === 'Other') {
        regexp = /\W/;
      }

      if (searchString.charAt(0).match(regexp) !== null) {
        return true;
      } else {
        return false;
      }
    });
  };
});

mach2Filters.filter('dateFilter', function() {
  return function(items, search) {
    return items.filter(function(element, index, array) {
      var albumDate    = moment(element.date, 'YYYY-MM-DD');
      var compDate     = moment(search, 'YYYY');
      var compNextDate = moment((parseInt(search) + 10), 'YYYY');

      return (albumDate.isAfter(compDate) && albumDate.isBefore(compNextDate));
    }); 
  };
});