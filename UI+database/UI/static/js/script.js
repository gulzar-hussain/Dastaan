var map;
function initMap() {
  map = new google.maps.Map(document.getElementById("map"), {
    center: { lat: 24.863455346089644, lng: 67.02731964264507 },
    zoom: 16,
    mapId: "dc97abf1022949ca",
  });
  const locations = [
    //add more locations
    ["Empress Market", 24.863455346089644, 67.02731964264507, 1],
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
}

window.initMap = initMap;
document.getElementById('btn-current-location').addEventListener('click', function() {
  document.getElementById('map').style.display = 'block'; // Replace with your modal or div ID
  initMap();
});

// Close the modal or div when the close button is clicked
document.getElementById('btn-close').addEventListener('click', function() {
  document.getElementById('map').style.display = 'none'; // Replace with your modal or div ID
});