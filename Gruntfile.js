module.exports = function(grunt) {
  var path = require("path");

  grunt.initConfig({
    pkg: grunt.file.readJSON("package.json"),
    bower: {
      install: {
        options: {
          targetDir: "static/scripts/libs",
          install: true,
          cleanup: true,
          layout: "byComponent"
        }
      }
    },
    run: {
      mach2: {
         cmd: "python",
         args: ["mach2.py"]
      }
    }
  });

  grunt.loadNpmTasks("grunt-bower-task");
  grunt.loadNpmTasks("grunt-run");

  grunt.task.registerTask("default", ["bower:install", "run:mach2"]);
};
