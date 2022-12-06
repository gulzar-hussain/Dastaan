var map;
function initMap() {
    map=new google.maps.Map(document.getElementById('map'), {
        center: {lat: 24.863455346089644 , lng: 67.02731964264507},
        zoom: 16,
        mapId: 'dc97abf1022949ca',
      });
      setMarkers(map)
       
}

const locations = [ 
  //add more locations
  ["Empress Market", 24.863455346089644, 67.02731964264507, 1],
];


function setMarkers(map){
  const image ={
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
  
    new google.maps.Marker({
      position: { lat: location[1], lng: location[2] },
      map,
      icon: image,
      shape: shape,
      title: location[0],
      zIndex: location[3],
    });
  }
}


window.initMap = initMap;

