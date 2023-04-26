window.addEventListener('DOMContentLoaded', event => {

  // Navbar shrink function
  var navbarShrink = function () {
      const navbarCollapsible = document.body.querySelector('#mainNav');
      if (!navbarCollapsible) {
          return;
      }
      if (window.scrollY === 0) {
          navbarCollapsible.classList.remove('navbar-shrink')
      } else {
          navbarCollapsible.classList.add('navbar-shrink')
      }

  };

  // Shrink the navbar 
  navbarShrink();

  // Shrink the navbar when page is scrolled
  document.addEventListener('scroll', navbarShrink);

  // Activate Bootstrap scrollspy on the main nav element
  const mainNav = document.body.querySelector('#mainNav');
  if (mainNav) {
      new bootstrap.ScrollSpy(document.body, {
          target: '#mainNav',
          offset: 74,
      });
  };

    


  // Collapse responsive navbar when toggler is visible
  const navbarToggler = document.body.querySelector('.navbar-toggler');
  const responsiveNavItems = [].slice.call(
      document.querySelectorAll('#navbarResponsive .nav-link')
  );
  responsiveNavItems.map(function (responsiveNavItem) {
      responsiveNavItem.addEventListener('click', () => {
          if (window.getComputedStyle(navbarToggler).display !== 'none') {
              navbarToggler.click();
          }
      });
  });




});


var map;
var geocoder;
function initMap() {
  // Try HTML5 geolocation
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      function (position) {
        const pos = {
          lat: position.coords.latitude,
          lng: position.coords.longitude,
        }
        map = new google.maps.Map(document.getElementById("map"), {
          center: pos,
          zoom: 16,
          mapId: "dc97abf1022949ca",
        });
        geocoder = new google.maps.Geocoder();
        const locations = [
          //add more locations
          ["Empress Market", 24.863455346089644, 67.02731964264507, 1],
          ["Your Cuurent Location", pos.lat,pos.lng, 1],
        ];
        const contentString =
    '<div id="content">' +
    '<div id="siteNotice">' +
    "</div>" +
    '<h1 id="firstHeading" class="firstHeading">Empress Market</h1>' +
    '<div id="bodyContent">' +
    '<img src="https://www.jagahonline.com/blog/wp-content/uploads/2021/07/Historical-Background-2.jpg" alt="Empress Market" width="150" height="160">' +
    "<p><b>Empress Market</b>, Lorem epsom is simply dummy text of the printing " +
    "and typesetting industry. southern part of the " +
    "Northern Territory, central Australia. It lies 335&#160;km (208&#160;mi) " +
    "south west of the nearest large town, Alice Springs; 450&#160;km " +
    "(280&#160;mi) by road. Kata Tjuta and Uluru are the two major " +
    "features of the Uluru - Kata Tjuta National Park. Uluru is " +
    "sacred to the Pitjantjatjara and Yankunytjatjara, the " +
    "Aboriginal people of the area. It has many springs, waterholes, " +
    "rock caves and ancient paintings. Uluru is listed as a World " +
    "Heritage Site.</p>" +
    "</div>" +
    "</div>";
        const infowindow = new google.maps.InfoWindow({
          content: contentString,
          ariaLabel: "Empress Market",
        });

        const image = {
          //url of image
          url: "https://developers.google.com/maps/documentation/javascript/examples/full/images/beachflag.png",
          size: new google.maps.Size(20, 32),
          origin: new google.maps.Point(0, 0),
          // The anchor for this image is the base of the flagpole at (0, 32).
          anchor: new google.maps.Point(0, 100),
        };
        const shape = {
          coords: [1, 1, 1, 20, 18, 20, 18, 1],
          type: "poly",
        };

        for (let i = 0; i < locations.length; i++) {
          const location = locations[i];

          const Marker = new google.maps.Marker({
            position: { lat: location[1], lng: location[2] },
            map,
            icon: image,
            shape: shape,
            title: location[0],
            zIndex: location[3],
          });
          Marker.addListener("click", () => {
            infowindow.open({
              anchor: Marker,
              map,
            });
          });
        }

        // Add a click event listener to the map
        map.addListener("click", (event) => {
          // Get the clicked location's address using the geocoder service
          geocoder.geocode({ location: event.latLng }, (results, status) => {
            if (status === "OK") {
              if (results[0]) {
                // Set the location name input field value to the clicked location's address
                document.getElementById("location_name").value = results[0].formatted_address;
              }
            }
          });
        });
      });
  }
}
const btnCurrentLocation = document.getElementById("btn-current-location");
const mapDiv = document.getElementById("map");
window.initMap = initMap;
document.getElementById('btn-current-location').addEventListener('click', function() {
  console.log('js-click');
  // Create the map div if it doesn't exist
  if (!mapDiv) {
    const newMapDiv = document.createElement("div");
    newMapDiv.id = "map";
    newMapDiv.style.display = "block";
    btnCurrentLocation.parentNode.appendChild(newMapDiv);
    initMap();
  } else {
    // Show the map div if it already exists
    initMap();
    mapDiv.style.display = "block";
  }
});


$(document).on("click", function (event) {
  if (
    !$(event.target).closest("#map").length &&
    !$(event.target).is("#btn-current-location")
  ) {
    $("#map").hide();
  }
});




