tmplt = """
{% block content %}
<!DOCTYPE html>
<head>
   <script>
      function openSection(evt, sectionName) {
        // Declare all variables
        var i, tabcontent, tablinks;
      
        // Get all elements with class="tabcontent" and hide them
        tabcontent = document.getElementsByClassName("tabcontent");
        for (i = 0; i < tabcontent.length; i++) {
          tabcontent[i].style.display = "none";
        }
      
        // Get all elements with class="tablinks" and remove the class "active"
        tablinks = document.getElementsByClassName("tablinks");
        for (i = 0; i < tablinks.length; i++) {
          tablinks[i].className = tablinks[i].className.replace(" active", "");
        }
      
        // Show the current tab, and add an "active" class to the button that opened the tab
        document.getElementById(sectionName).style.display = "block";
        evt.currentTarget.className += " active";
      
        document.getElementById('io_table_stats_btn').click();
      } 
      
      function openSubSection(evt, sectionName) {
        // Declare all variables
        var i, tabcontent, tablinks;
      
        // Get all elements with class="tabcontentSub" and hide them
        tabcontent = document.getElementsByClassName("tabcontentSub");
        for (i = 0; i < tabcontent.length; i++) {
          tabcontent[i].style.display = "none";
        }
      
        // Get all elements with class="tablinksSub" and remove the class "active"
        tablinks = document.getElementsByClassName("tablinksSub");
        for (i = 0; i < tablinks.length; i++) {
          tablinks[i].className = tablinks[i].className.replace(" active", "");
        }
      
        // Show the current tab, and add an "active" class to the button that opened the tab
        document.getElementById(sectionName).style.display = "block";
        evt.currentTarget.className += " active";
      } 
      
   </script>


<style>.container:before {
   content: "";
   position: absolute;
   top: 0;
   bottom: 0;
   left: 0;
   right: 0;
   z-index: 1;
   background-repeat: no-repeat;
   background-position: center;
   background-attachment: fixed;
   opacity: 0.1;
}

.content {
   position: relative;
   z-index: 1;
}

.tab {
   overflow: hidden;
   border: 1px solid #ccc;
}


/* Style the buttons that are used to open the tab content */

.tab button {
   background-color: inherit;
   float: left;
   border: none;
   outline: none;
   cursor: pointer;
   padding: 14px 16px;
   transition: 0.3s;
   font-weight: bold;
   font-size: medium;
}


/* Change background color of buttons on hover */

.tab button:hover {
   background-color: #ddd;
}


/* Create an active/current tablink class */

.tab button.active {
   background-color: #ccc;
}


/* Style the tab content */

.tabcontent {
   display: none;
   padding: 6px 12px;
   border-top: none;
}

.tftable th {
   font-weight: bold;
   font-size: 14px;
   background-color: #D8D8D8;
   border-width: 1px;
   padding: 8px;
   border-style: solid;
   border-color: #008bb9;
   text-align: left;
}

.tftable tr:hover {
   font-weight: bold;
   background-color: #e8f4f8;
}

.tftable2 td {
   font-weight: bold;
   font-size: 14px;
   background-color: #ffcccb;
   border-width: 1px;
   padding: 8px;
   border-style: none;
   text-align: left;
}

h3 {
   text-align: left;
}

table {
   display: block;
   overflow-x: auto;
   white-space: wrap;
}

</style>


</head>
<body onload="document.getElementById('findings_btn').click();">
   <div class="container">
   <div class="content">
   <div id="overview">
      <div>
         <h2><b>Postgres Database Report</b></h2>
      </div>
      <div>
         <table>
            <th><h3>Snapshot Details</h3></th>
            <th><h3>Instance Details</h3></th>
            <th><h3>Instance Role Timeline</h3></th>
            <tr>
               <td valign="top" style="white-space: nowrap;">{{ snapshot_details }}</td>
               <td valign="top" style="white-space: nowrap;">{{ cluster_details }}</td>
               <td valign="top" style="white-space: nowrap;">{{ database_role_timeline }}</td>
            </tr>
         </table>
      </div>
   </div>
   <!-- Tab links -->
   <div class="tab">
      <button id="findings_btn" class="tablinks" onclick="openSection(event, 'findings')">Findings</button>
      <button class="tablinks" onclick="openSection(event, 'io')">I/O</button>
      <button class="tablinks" onclick="openSection(event, 'vacuum_efficiency')">Vacuum Efficiency</button>
      <button class="tablinks" onclick="openSection(event, 'parameters')">Parameters</button>
   </div>
   <!-- Tab content -->
   <div id="findings" class="tabcontent">
         <ul>
         <li>
            <a href="#recom">Recommendation</a>
         </li>
         <li>
            <a href="#we">Wait Events and Wait Event Types</a>
         </li>
         <li>
            <a href="#dbio">Database I/O</a>
         </li>
         <li>
            <a href="#topq">Top Query by I/O</a>
         </li>
      </ul>
      <h3 id="recom" >Recommendations</h3>
      {{snapshot_details_findings}}
      {{bgwriter_findings}}
      {{index_stats_findings}}
      {{table_stats_findings}}
      <a href="#overview">[back to menu]</a>
      <h3 id="we" >Wait Events and Wait Event Types</h3>\n
      {{ wait_events }}
      {{ wait_events_type }}
      <a href="#overview">[back to menu]</a>
      <h3 id="dbio" >Database I/O</h3>\n
      <h4>
         Breakdown of I/O contributed by the current sampled database and the other databases on the cluster. 
         Review the "I/O" section for more details.
      </h4>
      <p style="color:red;">I/O for current database</p>
      {{database_io}}
      <p style="color:red;">I/O for remaining database</p>
      {{remainder_io}}
      <a href="#overview">[back to menu]</a>
      <h3 id="topq">Top Query by I/O</h3>\n
      <h4>
         List of queries by contribution to Read I/O. Review the "I/O"-> "By SQL" section for more details
      </h4>
      {{findings_top_io_sql}}
   </div>
   <div id="vacuum_efficiency" class="tabcontent">
      {{vacuum_stats}}
   </div>
   <div id="parameters" class="tabcontent">
      <ul>
         <li>
            <a href="#par">Parameters</a>
         </li>
         <li>
            <a href="#par_tl">Changed Parameters Timeline</a>
         </li>
      </ul>
      <h2 id="par">Parameters</h2>
      <a href="#overview">[back to menu]</a>
      {{parameters}}
      <h2 id="par_tl">Changed Parameters Timeline</h2>
      <a href="#overview">[back to menu]</a>
      {{pg_setting_change_timeline}}
   </div>
   <div id="io" class="tabcontent">
      <div class="tab">
         <button id="io_table_stats_btn" class="tablinksSub" onclick="openSubSection(event, 'table_stats')">By Table</button>
         <button class="tablinksSub" onclick="openSubSection(event, 'index_stats')">By Index</button>
         <button class="tablinksSub" onclick="openSubSection(event, 'sqlio_stats')">By SQL</button>
         {% if not is_aurora %}
            <button class="tablinksSub" onclick="openSubSection(event, 'bgwriter_stats')">Background Writer</button>
         {% endif %}
      </div>
      <div id="table_stats" class="tabcontentSub">
         <ul>
            <li>
               <a href="#ts_hr">Top {{ limit }} in heap reads</a>
            </li>
            <li>
               <a href="#ts_ir">Top {{ limit }} in index reads</a>
            </li>
            <li>
               <a href="#ts_tr">Top {{ limit }} in toast reads</a>
            </li>
            <li>
               <a href="#ts_tir">Top {{ limit }} in toast index reads</a>
            </li>
            <li>
               <a href="#ts_hh">Top {{ limit }} in heap hits</a>
            </li>
            <li>
               <a href="#ts_ih">Top {{ limit }} in index hits</a>
            </li>
            <li>
               <a href="#ts_th">Top {{ limit }} in toast hits</a>
            </li>
            <li>
               <a href="#ts_tih">Top {{ limit }} in toast index hits</a>
            </li>
         </ul>
         <h2 id="ts_hr">Top {{ limit }} in heap reads</h2>
         <a href="#overview">[back to menu]</a>
         {{ table_heap_reads }}
         <h2 id="ts_ir">Top {{ limit }} in index reads</h2>
         <a href="#overview">[back to menu]</a>
         {{ table_index_reads }}
         <h2 id="ts_tr">Top {{ limit }} in toast reads</h2>
         <a href="#overview">[back to menu]</a>
         {{ table_toast_reads }}
         <h2 id="ts_tir">Top {{ limit }} in toast index reads</h2>
         <a href="#overview">[back to menu]</a>
         {{ table_toast_index_reads }}
         <h2 id="ts_hh">Top {{ limit }} in heap hits</h2>
         <a href="#overview">[back to menu]</a>
         {{ table_heap_hits }}
         <h2 id="ts_ih">Top {{ limit }} in index hits</h2>
         <a href="#overview">[back to menu]</a>
         {{ table_index_hits }}
         <h2 id="ts_th">Top {{ limit }} in toast hits</h2>
         <a href="#overview">[back to menu]</a>
         {{ table_toast_hits }}
         <h2 id="ts_tih">Top {{ limit }} in toast index hits</h2>
         <a href="#overview">[back to menu]</a>
         {{ table_toast_index_hits }}
      </div>
      <div id="index_stats" class="tabcontentSub">
         <ul>
            <li>
               <a href="#is_iu">Top {{ limit }} tables with most unused indexes</a>
            </li>         
            <li>
               <a href="#is_ir">Top {{ limit }} in index reads</a>
            </li>
            <li>
               <a href="#is_ih">Top {{ limit }} in index hits</a>
            </li>
         </ul>
         <h2 id="is_iu">Top {{ limit }} in most unused indexes</h2>
         <a href="#overview">[back to menu]</a>
         {{ index_usage }}
         <details>
            <summary>List of Unused Indexes ( Up to 500 displayed )</summary>
            {{ index_usage_2 }}
         </details>
         <h2 id="is_ir">Top {{ limit }} in index reads</h2>
         <a href="#overview">[back to menu]</a>
         {{ index_reads }}
         <h2 id="is_ih">Top {{ limit }} in index hits</h2>
         <a href="#overview">[back to menu]</a>
         {{ index_hits }}
      </div>
      <div id="bgwriter_stats" class="tabcontentSub">
         {{ bgwriter_stats }}
      </div>
      <div id="sqlio_stats" class="tabcontentSub">
         <ul>
            <li>
               <a href="#ss_sr">Top {{ limit }} SQL  in shared blocks read</a>
            </li>
            <li>
               <a href="#ss_sh">Top {{ limit }} SQL in shared blocks hit</a>
            </li>
            <li>
               <a href="#ss_sw">Top {{ limit }} SQL in shared blocks written</a>
            </li>
            <li>
               <a href="#ss_tr">Top {{ limit }} SQL in temp blocks read</a>
            </li>
            <li>
               <a href="#ss_tw">Top {{ limit }} SQL in temp blocks written</a>
            </li>
            {% if sql_stats_wg %}
            <li>
               <a href="#ss_wg">Top {{ limit }} SQL in wal generated</a>
            </li>
            {% endif %}
         </ul>
         <h2 id="ss_sr">Top {{ limit }} SQL  in shared blocks read</h2>
         <a href="#overview">[back to menu]</a>
         {{ sql_r_io_stats }}
         <h2 id="ss_sh">Top {{ limit }} SQL in shared blocks hit</h2>
         <a href="#overview">[back to menu]</a>
         {{ sql_h_io_stats }}
         <h2 id="ss_sw">Top {{ limit }} SQL in shared blocks written</h2>
         <a href="#overview">[back to menu]</a>
         {{ sql_w_io_stats }}
         <h2 id="ss_tr">Top {{ limit }} SQL in temp blocks read</h2>
         <a href="#overview">[back to menu]</a>
         {{sql_tr_stats}}
         <h2 id="ss_tw">Top {{ limit }} SQL in temp blocks written</h2>
         <a href="#overview">[back to menu]</a>
         {{sql_tw_stats}}
         {% if sql_stats_wg %}
         <h2 id="ss_wg">Top {{ limit }} SQL in wal generated</h2>
         <a href="#overview">[back to menu]</a>
         {{sql_stats_wg}}
         {% endif %}
      </div>
   </div>
   </div>
   </div>
</body>
{% endblock %}
"""
