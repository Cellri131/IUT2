<?xml version="1.0" encoding="iso-8859-1"?>

<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

   <xsl:output method="html" encoding="iso-8859-15" doctype-public="-//W3C//DTD HTML 5.01 Transitional//EN"/>

   <!-- *********************** -->
   <!--   VARIABLES GLOBALES    -->
   <!-- *********************** -->

   <!-- Répertoire relatif pour accéder aux ressources générales -->  
   <xsl:variable name="repRac"> <xsl:value-of select="document/propriete/@repertoireRac" /> </xsl:variable>

   <!-- Répertoire relatif pour accéder aux images spécifique -->
   <xsl:variable name="repSpec"><xsl:value-of select="document/propriete/@repertoireSpec" /></xsl:variable>

   <!-- Style de paragraphe lié à la css pl.css-->
   <xsl:variable name="style"><xsl:value-of select="document/propriete/@style" /></xsl:variable>

   <xsl:variable name="pair">0</xsl:variable>


   <!-- *********************** -->
   <!--  Modèle pour la Racine  -->
   <!-- *********************** -->
   <xsl:template match="/">
      
      <html>

         <head>
            <meta http-equiv="Content-Type" content="text/html,charset=iso-8859-1" />
            <link rel="stylesheet"  type="text/css" href="{$repRac}css/pl.css" />
            <title>
               <xsl:value-of select="document/entete/@promotion" /> - Departement Informatique
            </title>
         </head>


         <body height="100%" class="indexFond1" link="#0000c0" text="#000000" vlink="#0000ff" background="{document/propriete/@fond}">


               <!-- - - - - - - - - - - - - -->
               <!--          En tete        -->
               <!-- - - - - - - - - - - - - -->
               <xsl:apply-templates select="document/entete-gene"     />
               <xsl:apply-templates select="document/entete-promo"    />
               <xsl:apply-templates select="document/entete-matiere"  />
               
               <xsl:apply-templates select="document/cadre" />
                           
            
               <p class="{$style}">&#169;  Departement Informatique, IUT du Havre.</p>
               
         </body>

      </html>
   
   </xsl:template>




   <!-- *********************** -->
   <!--      EN TETE PROMO      -->
   <!-- *********************** -->
   <xsl:template match="entete-promo">
      
      <div style="display:table;width:100%" >
      <div class="cadresimple" style="display:table-cell;" >
         
         <table style="width:100%">
         
            <tr>
               <td align="center"><img src="{$repRac}image/logoUniv.gif"       alt="Universite du Havre" />     </td>
               <td align="center"><img src="{$repRac}image/di2009.gif"         alt="Département Informatique" /> </td>
               <td align="center"><img src="{$repRac}image/{@promotion}.gif"   alt="{@promotion}" />                   </td>
               <td align="center"><img src="{$repRac}image/annee.gif"          alt="{@annee}" />                </td>
            </tr>
            
         </table>
         
      </div>
      </div>
      
      <br />

   </xsl:template>

   <!-- *********************** -->
   <!--      EN TETE GENE       -->
   <!-- *********************** -->
   <xsl:template match="entete-gene">
      
      <div style="display:table;width:100%" >
      <div class="cadresimple" style="display: table-cell;" >
         
         <table style="width:100%">
            <tr>
               <td align="center"><img src="{$repRac}image/logoUniv.gif"   alt="Universite du Havre" />     </td>
               <td align="center"><img src="{$repRac}image/di2009.gif"     alt="Département Informatique" />
                                  <xsl:apply-templates select="@sous-titre"   /> 
               </td>
               <td align="center"><img src="{$repRac}image/annee.gif"  alt="{@annee}" />                </td>

            </tr>
         
         </table>
      </div>
      </div>
      
      <br />

   </xsl:template>


   <xsl:template match="@sous-titre" >
      <h3 class="{$style}H1"><xsl:value-of select="." /> </h3>
   </xsl:template>
   
   
   <!-- *********************** -->
   <!--     EN TETE MATIERE     -->
   <!-- *********************** -->
   
   <!--       °°°°°°°           -->
   <!--       EN TETE           -->
   <!--       °°°°°°°           -->
   <xsl:template match="entete-matiere">

      <div style="display:table;width:100%" >
         <div class="cadresimple" style="display: table-cell;" >
         
            <table border="0" style="width:100%" >
               <tr>
                  <td>
                     <a href="../index.html" ><img valign="top" src="{$repRac}/image/cadre/back.gif" border="0" /></a><img src="{$repRac}image/logoUniv.gif" alt="Universite du Havre" nosave="" align="bottom" border="0"  />
                  </td>
            
                  <td align="center">
                     <xsl:apply-templates select="@matiere"     /><xsl:apply-templates select="@logoMatiere" /> <br />
                     <xsl:apply-templates select="@responsable" />
                  </td>
            
                  <td align="right">
                     <img src="{$repRac}image/diMini2009.gif" alt="Departement Informatique" nosave="" border="0"  />
                  </td>
            
               </tr>
            </table>
                          
   
            <br /><br />

            <xsl:apply-templates  select="intervenants" />

       </div>
       </div>
       
       <br />

   </xsl:template>


   <xsl:template match="@matiere" >
      <h1><font color="#284084" face="arial, helvetica"><xsl:value-of select="." /></font></h1>
   </xsl:template>

   
   <!--      °°°°°°°°°°°°      -->
   <!--      LOGO MATIERE      -->
   <!--      °°°°°°°°°°°°      -->
   <xsl:template match="@logoMatiere" >
      <img src="{.}" alt="{../@matiere}" />
   </xsl:template>
  
  
   <!--      °°°°°°°°°°°°      -->
   <!--      Responsable       -->
   <!--      °°°°°°°°°°°°      -->
   <xsl:template match="@responsable">
      <b><font face="arial, helvetica"><font size="-1">
            responsable : &#160; <xsl:value-of select="../@responsable" />
         </font></font>
      </b>
   </xsl:template>   
   
   
   <!-- °°°°°°°°°°°°°°°°°°°°°° -->
   <!-- LISTE DES INTERVENANTS -->
   <!-- °°°°°°°°°°°°°°°°°°°°°° -->
   <xsl:template match="intervenants" >
      
            <table border="0" class="{$style}" style="width:100%" cellpadding="0" cellspacing="0">
               <font face="arial, helvetica"><font size="-1">
               <tr>
                  <td colspan="9"><b>Enseignants <xsl:value-of select="@type" /></b></td>
               </tr>  

               <xsl:for-each select="intervenant">
                   
                     <xsl:if test="position() mod 2=1"> 
                     <tr>
                     <td valign="top" width="40"><xsl:value-of select="@civ"    /> &#160; </td>
                     <td valign="top" width="90"><xsl:value-of select="@nom"    /> &#160; </td>
                     <td valign="top" ><xsl:value-of select="@prenom" /> &#160; </td>
                     <td valign="top"><a class="javaLien" href="mailto:{@mail}"><xsl:value-of select="@mail" /></a></td>

                     <td width="30" />                        

                     <td valign="top" width="40"><xsl:value-of select="./following-sibling::intervenant/@civ"    /> &#160; </td>
                     <td valign="top" width="90"><xsl:value-of select="./following-sibling::intervenant/@nom"    /> &#160; </td>
                     <td valign="top"><xsl:value-of select="./following-sibling::intervenant/@prenom" /> &#160; </td>
                     <td valign="top"><a class="javaLien" href="mailto:{./following-sibling::intervenant/@mail}"><xsl:value-of select="./following-sibling::intervenant/@mail" /></a></td>

                     </tr>
                     </xsl:if>

                     
                   

               </xsl:for-each>

               <tr> <td colspan="9">&#160;  </td></tr>

               </font></font>
            </table>
         
   </xsl:template>




   <!-- *********************** -->
   <!--          CADRE          -->
   <!-- *********************** -->
	<xsl:template match="cadre[@type='vide']">
		<xsl:apply-templates />
	</xsl:template>
	
	
   <xsl:template match="cadre[@type='simple']">
      
      <div style="display:table;width:100%" >
         <div class="cadresimple" style="display: table-cell;" >
             <xsl:apply-templates select="cellule" />
         </div>
      </div>
      <br />
      
   </xsl:template>

   <xsl:template match="cadre[@type='double']">
      
      <div style="display:table;width:100%;" >
            <div style="display:table-row;">
                <div  class="cadredouble" style="display:table-cell;{@style}" >
                  <xsl:apply-templates select="cellule[position()=1]" />    
                </div>
                
                <div style="display:table-cell;" >&#160;&#160;</div>
                
                <div  class="cadredouble" style="display:table-cell;{@style}" >
                  <xsl:apply-templates select="cellule[position()=2]" />
                </div>
            </div>
       </div>
       <br />
      
   </xsl:template>

   

   <xsl:template match="cadreCentre|cadreGauche|cadreDroit">
		
               <h3 class="{$style}H1"><xsl:value-of select="@titre" /> </h3>
               <xsl:apply-templates  />
		
   </xsl:template>

   <xsl:template match="cellule">
               	<h3 class="{$style}H1"><xsl:value-of select="@titre" /> </h3>
               	<xsl:apply-templates  />
   </xsl:template>


   <!-- *********************** -->
   <!--          LISTE          -->
   <!-- *********************** -->
   <xsl:template match="liste">
   
      <table class="{$style}">
         <xsl:for-each select="ligne">
            <tr>
               <td>  
                  <a class="{$style}lien" href="{sujet/@dest}"><xsl:value-of select="sujet" /></a>
                  <xsl:apply-templates select="sous-sujet" />
               </td>
               <td valign="top">
                  &#160;<xsl:value-of select="duree" />
               </td>
               <td>
                  &#160;&#160;<a class="{$style}lien" href="{corrige/@dest}"><xsl:value-of select="corrige" /></a>
               </td>
            </tr>
         </xsl:for-each>
      </table>
   </xsl:template>    
   
   <xsl:template match="sous-sujet">
   
      <br />&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;
      
      <xsl:value-of select="." />
      
   
   </xsl:template>
   
   
   <!-- *********************** -->
   <!--       PARAGRAPHE        -->
   <!-- *********************** -->
   <xsl:template match="para">
      <p class="{$style}" >
         <xsl:apply-templates />
      </p>
   </xsl:template>    
 
   <xsl:template match="centrer">
       <center><xsl:apply-templates /></center>
   </xsl:template>
 
   <!-- *********************** -->
   <!--          LIEN           -->
   <!-- *********************** -->
   <xsl:template match="lien">
       
       <a class="mlienindex" href="{@dest}" align="center">
       <!-- <a class="mlien{$style}" href="{@dest}" align="center">-->
       <!--<a class="{$style}lien" href="{@dest}" align="center"> -->
            <xsl:choose>
               <xsl:when test="@image='aucune'">
                  <xsl:apply-templates />      
               </xsl:when>
               <xsl:otherwise>
                  <table class="{$style}lien">
                     <tr><td align="center">
                           <a class="{$style}lien" href="{@dest}" >
                              <img src="{@image}" title="{@image}" border="0"/><br />
                              <xsl:value-of select="." />
                           </a>
                     </td></tr>
                  </table>
               </xsl:otherwise>
            </xsl:choose>
      </a>
   </xsl:template>





   <!-- *********************** -->
   <!--      MISE EN FORME      -->
   <!-- *********************** -->
   <xsl:template match="g">      <b><xsl:apply-templates /></b>   </xsl:template>
   <xsl:template match="i">      <i><xsl:apply-templates /></i>   </xsl:template>
   <xsl:template match="s">      <u><xsl:apply-templates /></u>   </xsl:template>
   <xsl:template match="t">      &#160;&#160;                     </xsl:template>
   <xsl:template match="br">     <br />                           </xsl:template>
   <xsl:template match="puce">   &#160;&#160;&#8226;&#160;        </xsl:template>

   <xsl:template match="coul">
      <font color="{@val}"><xsl:apply-templates /></font>
   </xsl:template>

  <!-- Traduction des ~ par un blanc -->
  <xsl:template match="text()">
      <xsl:call-template name="traduction">
         <xsl:with-param name="texte" select="."/>
      </xsl:call-template>
   </xsl:template>

  <xsl:template name="traduction" >
   <xsl:param name="texte" />
      <xsl:variable name="t1"><xsl:value-of select="translate($texte,'¨','&#160;')"/></xsl:variable>
      <xsl:value-of select="$t1" />
   </xsl:template>

   <!-- *********************** -->
   <!--         IMAGE           -->
   <!-- *********************** -->
   <xsl:template match="image">
      <img>
         <xsl:attribute name="src">   <xsl:value-of select="@fichier" /> </xsl:attribute>

         <xsl:choose>
            <xsl:when test="@hauteur='original'"></xsl:when>
            <xsl:otherwise>
               <xsl:attribute name="height">
                  <xsl:value-of select="@hauteur" />
               </xsl:attribute> 
            </xsl:otherwise>
         </xsl:choose>
         
         <xsl:choose>
            <xsl:when test="@largeur='original'"></xsl:when>
            <xsl:otherwise>
               <xsl:attribute name="width">
                  <xsl:value-of select="@largeur" />
               </xsl:attribute> 
            </xsl:otherwise>
         </xsl:choose>

      </img>
      
   </xsl:template>

   <!-- *********************** -->
   <!--         TABLEAU         -->
   <!-- *********************** -->
   <xsl:template match="tableau">
        
      <table name="class" style="{@style}">
         <xsl:attribute name="class"><xsl:value-of select="$style" /></xsl:attribute>
         <xsl:apply-templates />
      </table>
            
   </xsl:template>
   

   <xsl:template match="ligne">
         <tr class="table-ligne{@n}">
            <xsl:apply-templates />
         </tr>
   </xsl:template>

   <xsl:template match="case">
         <td rowspan="{@rowspan}" colspan="{@colspan}" style="{@style}" >
            <xsl:apply-templates />
         </td>
   </xsl:template>
 
</xsl:stylesheet>
