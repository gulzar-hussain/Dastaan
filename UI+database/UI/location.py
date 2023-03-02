#  <!-- <script>
#             function addRowHandlers() {
#                 var table = document.getElementById("tableId");
#                 var rows = table.getElementsByTagName("tr");
                
#                 for (i = 0; i < rows.length; i++) {
#                     var currentRow = table.rows[i];
                    
#                     var createClickHandler = 
#                         function(row) 
#                         {
#                             return function() { 
#                                                     var cell = row.getElementsByTagName("td")[0];
#                                                     var id = cell.innerHTML;
#                                                     var url = "{{ url_for('getlocations')}}";

#                         // Redirect to the Flask route that renders the desired template
#                                                     window.location.href = url;
#                                              };
#                         };
            
#                     currentRow.onclick = createClickHandler(currentRow);
#                 }

               
#             }
#             window.onload = addRowHandlers();
#             </script> -->

#  def getLocation(address):
#     geolocator = Nominatim(user_agent="Your_Name")
#     location = geolocator.geocode(address)
#     if location is not None:
#         conn, cur = get_db_connection()
#         cur.execute("INSERT INTO locations (longitude, latitude, location_data) VALUES (%s, %s, ST_SetSRID(ST_GeomFromText('POINT(' || %s || ' ' || %s || ')'), 4326)) RETURNING id", (location.longitude, location.latitude, location.longitude, location.latitude))
#         location_id = cur.fetchone()[0]
#         cur.close()
#         conn.commit()
#         return location_id
#     else:
#         return None