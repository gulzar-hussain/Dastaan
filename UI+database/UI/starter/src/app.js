// Copyright 2021 Google LLC

// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at

//     https://www.apache.org/licenses/LICENSE-2.0

// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

import { Loader } from "@googlemaps/js-api-loader";
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
const geometry = new THREE.BufferGeometry();
const apiOptions = {
  apiKey: "AIzaSyCKzhctx7LyYpC0R5RUaoNMm_UOHuELP4c",
  version: "beta",
  libraries: ["places"],
};
// Old:AIzaSyAZ5HIzVkOyv-Y92om1I1JV08UIthSRLJA
// New: AIzaSyCKzhctx7LyYpC0R5RUaoNMm_UOHuELP4c
let mapOptions = {
  tilt: 0,
  heading: 0,
  zoom: 18,
  center: { lat: 0, lng: 0 },
  mapId: "4a9b9222ea5d497a",
};
// Old:2f95a159e490bcec
// New: 4a9b9222ea5d497a

async function initMap() {
  const mapDiv = document.getElementById("map");
  const apiLoader = new Loader(apiOptions);
  await apiLoader.load();

  return new google.maps.Map(mapDiv, mapOptions);
}

function initWebGLOverlayView(map) {
  let scene, renderer, camera, loader;
  const webGLOverlayView = new google.maps.WebGLOverlayView();

  webGLOverlayView.onAdd = () => {
    // set up the scene
    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera();
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.75); // soft white light
    scene.add(ambientLight);
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.25);
    directionalLight.position.set(0.5, -1, 0.5);
    scene.add(directionalLight);

    // load the model
    loader = new GLTFLoader();
    const source = "pin.gltf";
    loader.load(source, (gltf) => {
      gltf.scene.scale.set(25, 25, 25);
      gltf.scene.rotation.x = (180 * Math.PI) / 180; // rotations are in radians
      scene.add(gltf.scene);
    });
  };

  webGLOverlayView.onContextRestored = ({ gl }) => {
    // create the three.js renderer, using the
    // maps's WebGL rendering context.
    renderer = new THREE.WebGLRenderer({
      canvas: gl.canvas,
      context: gl,
      ...gl.getContextAttributes(),
    });
    renderer.autoClear = false;

    // wait to move the camera until the 3D model loads
    loader.manager.onLoad = () => {
      renderer.setAnimationLoop(() => {
        map.moveCamera({
          tilt: mapOptions.tilt,
          heading: mapOptions.heading,
          zoom: mapOptions.zoom,
        });

        // rotate the map 360 degrees
        if (mapOptions.tilt < 67.5) {
          mapOptions.tilt += 0.5;
        }
        // else if (mapOptions.heading <= 360) {
        //   mapOptions.heading += 0.2;
        // }
        else {
          renderer.setAnimationLoop(null);
        }
      });
    };
  };

  webGLOverlayView.onDraw = ({ gl, transformer }) => {
    // update camera matrix to ensure the model is georeferenced correctly on the map
    const latLngAltitudeLiteral = {
      lat: mapOptions.center.lat,
      lng: mapOptions.center.lng,
      altitude: 120,
    };

    const matrix = transformer.fromLatLngAltitude(latLngAltitudeLiteral);
    camera.projectionMatrix = new THREE.Matrix4().fromArray(matrix);

    webGLOverlayView.requestRedraw();
    renderer.render(scene, camera);

    // always reset the GL state
    renderer.resetState();
  };
  webGLOverlayView.setMap(map);
}
function iwClick(lat, lng) {
  fetch("http://127.0.0.1:5000/mapcoordinates", {
    method: "POST",
    body: JSON.stringify({ lat: lat, lng: lng }),
    headers: { "Content-Type": "application/json" },
  })
  .then((response) => {
    const url = `http://127.0.0.1:5000/storiesviamap?lat=${lat}&lng=${lng}`;
    window.location.replace(url);
  })

  .catch((error) => console.error(error));
}


(async () => {
  const map = await initMap();
  initWebGLOverlayView(map);
  const karachiBounds = new google.maps.LatLngBounds(
    new google.maps.LatLng(24.78229, 66.956602),
    new google.maps.LatLng(25.157623, 67.328409)
  );
  const searchBox = new google.maps.places.Autocomplete(
    document.getElementById("pac-input"),
    { bounds: karachiBounds }
  );
  searchBox.addListener("place_changed", () => {
    const place = searchBox.getPlace();
    if (place.geometry) {
      const bounds = new google.maps.LatLngBounds();
      bounds.extend(place.geometry.location);
      map.fitBounds(bounds);
      map.setZoom(20);
    } else {
      console.error("Error: No location found for the selected place.");
    }
  });
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      function (position) {
        var pos = {
          lat: position.coords.latitude,
          lng: position.coords.longitude,
        };
        // Update the map's center to the user's current location
        map.setCenter(pos);
      },
      function () {
        // Handle errors if geolocation is not supported or permission is denied
        console.error("Error: The Geolocation service failed.");
      }
    );
  } else {
    // Handle errors if geolocation is not supported
    console.error("Error: Your browser doesn't support geolocation.");
  }

  map.addListener("click", (event) => {
    // Get the coordinates of the clicked location
    const lat = event.latLng.lat();
    const lng = event.latLng.lng();
    let buttonName = "Go To Stories";
    const infoWindow = new google.maps.InfoWindow({});
    var div = document.createElement("div");
    div.innerHTML =
      '<i class="fa fa-book"  style="font-size: 50px; display:block; margin-left:auto; margin-right:auto; text-align:center"></i><br>';
    div.innerHTML += buttonName;
    div.onclick = function () {
      iwClick(lat, lng);
    };

    infoWindow.setContent(div);

    // Set the position of the info window to the clicked location
    infoWindow.setPosition(event.latLng);

    // Open the info window
    infoWindow.open(map);
  });
// GET ALL STORIES AND LOCATION_DATA
let Locations =[];
fetch('http://127.0.0.1:5000/locationData')
.then(response => response.json())
.then(data => {
  // Access lat and long data from the JSON response
  const stories = data;
  
  for (const story of stories) {
    
    const lat = story.latitude;
    const lng = story.longitude;
    let loc=new google.maps.LatLng(lat,lng);
    Locations.push(loc); 
    // Other data like location, location_data (point) and story_id can also be accessed.
    // console.log(`Location: ${story.location},Latitude: ${lat}, Longitude: ${lng}`);
  }
  console.log(Locations);
  var markers = [];

  // Loop through the locations array and create a marker for each one
  for (var i = 0; i < Locations.length; i++) {
    console.log('here in for loop');
    var marker = new google.maps.Marker({
      position: Locations[i],
      map: map
    });

    // Add a click event listener to the marker to open the info window
    marker.addListener('click', (function(marker) {
      return function() {
        const lat = marker.getPosition().lat();
        const lng = marker.getPosition().lng();
        let buttonName = "Go To Stories";
        const infoWindow = new google.maps.InfoWindow({});
        var div = document.createElement("div");
        div.innerHTML =
          '<i class="fa fa-book"  style="font-size: 50px; display:block; margin-left:auto; margin-right:auto; text-align:center"></i><br>';
        div.innerHTML += buttonName;
        div.onclick = function () {
          iwClick(lat, lng);
        };

        infoWindow.setContent(div);

        infoWindow.open(map, marker);
      };
    })(marker));

    // Add the marker to the markers array
    markers.push(marker);
  }
})
.catch(error => console.error(error));


})();



  
