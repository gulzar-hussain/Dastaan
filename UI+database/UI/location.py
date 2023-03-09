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

